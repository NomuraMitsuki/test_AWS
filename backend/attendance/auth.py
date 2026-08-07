"""JWT claims / ロール判定ヘルパ。

API Gateway HTTP API JWT authorizer は
`event.requestContext.authorizer.jwt.claims` にクレームを載せる。
"""

from __future__ import annotations


def get_jwt_claims(event: dict) -> dict | None:
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    except (KeyError, TypeError):
        return None
    if not isinstance(claims, dict):
        return None
    return claims


def get_cognito_sub(claims: dict) -> str | None:
    sub = claims.get("sub")
    return str(sub) if sub else None


def get_email(claims: dict) -> str | None:
    email = claims.get("email")
    return str(email) if email else None


def get_cognito_groups(claims: dict) -> list[str]:
    raw = claims.get("cognito:groups")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(g) for g in raw]
    # 単一グループ時は文字列、複数はスペース区切りや JSON 配列文字列のことがある
    text = str(raw).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"').strip("'") for part in inner.split(",") if part.strip()]
    return text.split()


def request_id_from_event(event: dict) -> str:
    try:
        rid = event["requestContext"]["requestId"]
        if rid:
            return str(rid)
    except (KeyError, TypeError):
        pass
    return "unknown"
