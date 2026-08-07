"""API Gateway HTTP API (payload 2.0) — ユーザールート。"""

from __future__ import annotations

import json
import re
from typing import Optional

from auth import request_id_from_event
from cognito import CognitoClient, default_cognito_client
from errors import AppError, error_body
from repository import InMemoryUserRepository, UserRepository
from service import UserService

_default_repo: Optional[UserRepository] = None
_default_cognito: Optional[CognitoClient] = None

_PATCH_RE = re.compile(r"^PATCH /users/([^/]+)$")


def get_repository() -> UserRepository:
    global _default_repo
    if _default_repo is None:
        # 本番接続は後続で差し替え。単体テストは repo 引数で注入する。
        _default_repo = InMemoryUserRepository()
    return _default_repo


def get_cognito() -> CognitoClient:
    global _default_cognito
    if _default_cognito is None:
        _default_cognito = default_cognito_client()
    return _default_cognito


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


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


def _path_param(event: dict, name: str) -> Optional[str]:
    params = event.get("pathParameters") or {}
    value = params.get(name)
    return str(value) if value else None


def _json_body(event: dict) -> dict:
    raw = event.get("body")
    if raw is None or raw == "":
        return {}
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AppError(400, "BAD_REQUEST", "JSON ボディが不正です") from exc
    if not isinstance(data, dict):
        raise AppError(400, "BAD_REQUEST", "JSON オブジェクトが必要です")
    return data


def _user_id_from_route(event: dict, route: str) -> str:
    user_id = _path_param(event, "id")
    if user_id and user_id != "{id}":
        return user_id
    match = _PATCH_RE.match(route)
    if match and match.group(1) != "{id}":
        return match.group(1)
    raise AppError(400, "BAD_REQUEST", "id パスパラメータが必要です")


def handler(
    event,
    context,
    repo: Optional[UserRepository] = None,
    cognito: Optional[CognitoClient] = None,
):
    request_id = request_id_from_event(event or {})
    repository = repo or get_repository()
    cognito_client = cognito or get_cognito()
    service = UserService(repository, cognito_client)

    try:
        route = _route_key(event or {})

        if route == "GET /users":
            items = service.list_users(event)
            return _response(200, {"items": [u.to_dict() for u in items]})

        if route == "POST /users":
            body = _json_body(event or {})
            email = body.get("email")
            name = body.get("name")
            role = body.get("role")
            if not email:
                raise AppError(400, "BAD_REQUEST", "email は必須です")
            if not name:
                raise AppError(400, "BAD_REQUEST", "name は必須です")
            if not role:
                raise AppError(400, "BAD_REQUEST", "role は必須です")
            manager_id = body.get("manager_id")
            user = service.invite_user(
                event,
                email=str(email),
                name=str(name),
                role=str(role),
                manager_id=str(manager_id) if manager_id is not None else None,
            )
            return _response(201, user.to_dict())

        if route == "PATCH /users/{id}" or _PATCH_RE.match(route):
            user_id = _user_id_from_route(event or {}, route)
            body = _json_body(event or {})
            kwargs: dict = {}
            if "name" in body:
                kwargs["name"] = body["name"]
            if "role" in body:
                kwargs["role"] = body["role"]
            if "manager_id" in body:
                kwargs["manager_id"] = body["manager_id"]
            if "status" in body:
                kwargs["status"] = body["status"]
            if not kwargs:
                raise AppError(400, "BAD_REQUEST", "更新フィールドがありません")
            user = service.update_user(event, user_id, **kwargs)
            return _response(200, user.to_dict())

        raise AppError(404, "NOT_FOUND", f"未知のルートです: {route}")

    except AppError as err:
        return _response(err.status_code, error_body(err.code, err.message, request_id))
    except Exception:
        return _response(
            500,
            error_body("INTERNAL_ERROR", "予期せぬエラーが発生しました", request_id),
        )
