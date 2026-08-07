"""API Gateway HTTP API (payload 2.0) — エクスポートルート。"""

from __future__ import annotations

import json
from datetime import date
from typing import Optional

from auth import request_id_from_event
from errors import AppError, error_body
from repository import ExportRepository, InMemoryExportRepository
from service import ExportService
from storage import StorageClient, default_storage_client

_default_repo: Optional[ExportRepository] = None
_default_storage: Optional[StorageClient] = None


def get_repository() -> ExportRepository:
    global _default_repo
    if _default_repo is None:
        # 本番接続は後続で差し替え。単体テストは repo 引数で注入する。
        _default_repo = InMemoryExportRepository()
    return _default_repo


def get_storage() -> StorageClient:
    global _default_storage
    if _default_storage is None:
        _default_storage = default_storage_client()
    return _default_storage


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_date(value: Optional[str], field: str) -> date:
    if value is None or value == "":
        raise AppError(400, "BAD_REQUEST", f"{field} は必須です")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppError(400, "BAD_REQUEST", f"{field} は YYYY-MM-DD 形式です") from exc


def _route_key(event: dict) -> str:
    if event.get("routeKey"):
        return str(event["routeKey"])
    try:
        method = event["requestContext"]["http"]["method"]
        path = event["requestContext"]["http"]["path"]
        return f"{method} {path}"
    except (KeyError, TypeError):
        method = event.get("httpMethod") or "GET"
        path = event.get("rawPath") or event.get("path") or ""
        return f"{method} {path}"


def _json_body(event: dict) -> dict:
    raw = event.get("body")
    if raw is None or raw == "":
        return {}
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AppError(400, "BAD_REQUEST", "JSON ボディが不正です") from exc
    if not isinstance(parsed, dict):
        raise AppError(400, "BAD_REQUEST", "JSON オブジェクトが必要です")
    return parsed


def handler(
    event,
    context,
    repo: Optional[ExportRepository] = None,
    storage: Optional[StorageClient] = None,
):
    request_id = request_id_from_event(event or {})
    repository = repo or get_repository()
    storage_client = storage or get_storage()
    service = ExportService(repository, storage_client)

    try:
        route = _route_key(event or {})

        if route == "POST /exports/attendance":
            body = _json_body(event or {})
            from_date = _parse_date(body.get("from_date"), "from_date")
            to_date = _parse_date(body.get("to_date"), "to_date")
            scope = body.get("scope")
            if scope is None or scope == "":
                raise AppError(400, "BAD_REQUEST", "scope は必須です")
            result = service.export_attendance(
                event,
                from_date=from_date,
                to_date=to_date,
                scope=str(scope),
            )
            return _response(200, result)

        raise AppError(404, "NOT_FOUND", f"未知のルートです: {route}")

    except AppError as err:
        return _response(err.status_code, error_body(err.code, err.message, request_id))
    except Exception:
        return _response(
            500,
            error_body("INTERNAL_ERROR", "予期せぬエラーが発生しました", request_id),
        )
