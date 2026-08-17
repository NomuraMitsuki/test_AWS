"""RDS マイグレーション / 初回 admin シード。HTTP API には公開しない。

Lambda イベント（API Gateway 形式ではない）:
  {} または {"action": "migrate"}
      backend/migrations/*.sql をファイル名順で適用
  {"action": "seed_admin", "email": "...", "cognito_sub": "...", "name": "..."}
      users に admin/active を INSERT。Cognito は呼ばない
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from db import connect_from_secret, load_db_secret

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_MIGRATIONS_DIR_IN_PACKAGE = Path(__file__).resolve().parent / "migrations"
_MIGRATIONS_DIR_IN_REPO = Path(__file__).resolve().parents[1] / "migrations"


def migrations_dir(override: Optional[Path] = None) -> Path:
    if override is not None:
        return Path(override)
    if _MIGRATIONS_DIR_IN_PACKAGE.is_dir():
        return _MIGRATIONS_DIR_IN_PACKAGE
    return _MIGRATIONS_DIR_IN_REPO


def list_migration_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.glob("*.sql") if p.is_file())


def apply_migrations(conn, directory: Path) -> list[str]:
    applied: list[str] = []
    files = list_migration_files(directory)
    if not files:
        raise FileNotFoundError(f"SQL マイグレーションが見つかりません: {directory}")
    for path in files:
        sql = path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
        applied.append(path.name)
    conn.commit()
    return applied


def _row_to_user(row: Any) -> dict:
    if isinstance(row, dict):
        return {
            "id": str(row["id"]),
            "cognito_sub": row["cognito_sub"],
            "email": row["email"],
            "name": row["name"],
            "role": row["role"],
            "status": row["status"],
        }
    return {
        "id": str(row[0]),
        "cognito_sub": row[1],
        "email": row[2],
        "name": row[3],
        "role": row[4],
        "status": row[5],
    }


def seed_admin(conn, email: str, cognito_sub: str, name: str) -> dict:
    email_n = email.strip()
    sub_n = cognito_sub.strip()
    name_n = name.strip()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, cognito_sub, email, name, role, status
            FROM users
            WHERE email = %s OR cognito_sub = %s
            """,
            (email_n, sub_n),
        )
        existing = cur.fetchall() or []

    if len(existing) > 1:
        return {
            "ok": False,
            "action": "seed_admin",
            "code": "CONFLICT",
            "error": "email と cognito_sub が別の users 行に紐づいています",
        }
    if len(existing) == 1:
        user = _row_to_user(existing[0])
        if user["email"].lower() != email_n.lower() or user["cognito_sub"] != sub_n:
            return {
                "ok": False,
                "action": "seed_admin",
                "code": "CONFLICT",
                "error": "既存行の email または cognito_sub が指定と一致しません",
            }
        return {
            "ok": True,
            "action": "seed_admin",
            "created": False,
            "user": user,
        }

    user_id = str(uuid4())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, cognito_sub, email, name, role, status)
                VALUES (%s, %s, %s, %s, 'admin', 'active')
                RETURNING id, cognito_sub, email, name, role, status
                """,
                (user_id, sub_n, email_n, name_n),
            )
            row = cur.fetchone()
        conn.commit()
    except Exception as exc:
        if type(exc).__name__ != "UniqueViolation":
            raise
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, cognito_sub, email, name, role, status
                FROM users
                WHERE email = %s OR cognito_sub = %s
                """,
                (email_n, sub_n),
            )
            row = cur.fetchone()
        if row is None:
            raise
        return {
            "ok": True,
            "action": "seed_admin",
            "created": False,
            "user": _row_to_user(row),
        }

    return {
        "ok": True,
        "action": "seed_admin",
        "created": True,
        "user": _row_to_user(row),
    }


def _event_action(event: dict) -> str:
    action = event.get("action")
    if action is None or action == "":
        return "migrate"
    return str(action)


def handler(event=None, context=None, *, conn=None, migrations_dir_override: Optional[Path] = None):
    event = event or {}
    if not isinstance(event, dict):
        return {
            "ok": False,
            "action": "unknown",
            "code": "BAD_REQUEST",
            "error": "イベントは JSON オブジェクトである必要があります",
        }

    action = _event_action(event)
    own_conn = False
    if conn is None:
        arn = os.environ.get("DB_SECRET_ARN")
        if not arn:
            raise RuntimeError("環境変数 DB_SECRET_ARN が未設定です")
        secret = load_db_secret(arn)
        conn = connect_from_secret(secret)
        own_conn = True

    try:
        if action == "migrate":
            applied = apply_migrations(conn, migrations_dir(migrations_dir_override))
            logger.info("migrations applied: %s", applied)
            return {"ok": True, "action": "migrate", "applied": applied}

        if action == "seed_admin":
            email = event.get("email")
            cognito_sub = event.get("cognito_sub")
            name = event.get("name")
            missing = [
                field
                for field, value in (
                    ("email", email),
                    ("cognito_sub", cognito_sub),
                    ("name", name),
                )
                if value is None or str(value).strip() == ""
            ]
            if missing:
                return {
                    "ok": False,
                    "action": "seed_admin",
                    "code": "BAD_REQUEST",
                    "error": f"必須フィールドがありません: {', '.join(missing)}",
                }
            return seed_admin(conn, str(email), str(cognito_sub), str(name))

        return {
            "ok": False,
            "action": action,
            "code": "BAD_REQUEST",
            "error": f"未知の action です: {action}",
        }
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        if own_conn:
            conn.close()
