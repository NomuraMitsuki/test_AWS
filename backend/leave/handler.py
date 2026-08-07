"""API Gateway HTTP API (payload 2.0) — 休暇ルート。"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Optional
from urllib.parse import parse_qs

from auth import request_id_from_event
from errors import AppError, error_body
from repository import InMemoryLeaveRepository, LeaveRepository
from service import LeaveService

_default_repo: Optional[LeaveRepository] = None

_APPROVE_RE = re.compile(r"^POST /leave-requests/([^/]+)/approve$")
_REJECT_RE = re.compile(r"^POST /leave-requests/([^/]+)/reject$")


def get_repository() -> LeaveRepository:
    global _default_repo
    if _default_repo is None:
        # 本番接続は後続で差し替え。単体テストは repo 引数で注入する。
        _default_repo = InMemoryLeaveRepository()
    return _default_repo


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


def _query_params(event: dict) -> dict:
    params = event.get("queryStringParameters") or {}
    if params:
        return params
    raw = event.get("rawQueryString") or ""
    if not raw:
        return {}
    parsed = parse_qs(raw, keep_blank_values=True)
    return {k: v[0] if v else "" for k, v in parsed.items()}


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


def _leave_id_from_route(event: dict, route: str, pattern: re.Pattern[str]) -> str:
    leave_id = _path_param(event, "id")
    if leave_id and leave_id != "{id}":
        return leave_id
    match = pattern.match(route)
    if match and match.group(1) != "{id}":
        return match.group(1)
    raise AppError(400, "BAD_REQUEST", "id パスパラメータが必要です")


def handler(event, context, repo: Optional[LeaveRepository] = None):
    request_id = request_id_from_event(event or {})
    repository = repo or get_repository()
    service = LeaveService(repository)

    try:
        route = _route_key(event or {})
        qs = _query_params(event or {})

        if route == "GET /leave-requests":
            scope = qs.get("scope") or "self"
            status = qs.get("status") or None
            if status == "":
                status = None
            items = service.list_leaves(event, scope=scope, status=status)
            return _response(200, {"items": [r.to_dict() for r in items]})

        if route == "POST /leave-requests":
            body = _json_body(event or {})
            leave_type = body.get("leave_type")
            if not leave_type:
                raise AppError(400, "BAD_REQUEST", "leave_type は必須です")
            start = _parse_date(body.get("start_date"), "start_date")
            end = _parse_date(body.get("end_date"), "end_date")
            comment = body.get("comment")
            leave = service.create_leave(
                event,
                leave_type=str(leave_type),
                start_date=start,
                end_date=end,
                comment=str(comment) if comment is not None else None,
            )
            return _response(201, leave.to_dict())

        if route == "POST /leave-requests/{id}/approve" or _APPROVE_RE.match(route):
            leave_id = _leave_id_from_route(event or {}, route, _APPROVE_RE)
            leave = service.approve(event, leave_id)
            return _response(200, leave.to_dict())

        if route == "POST /leave-requests/{id}/reject" or _REJECT_RE.match(route):
            leave_id = _leave_id_from_route(event or {}, route, _REJECT_RE)
            body = _json_body(event or {})
            reason = body.get("reject_reason")
            leave = service.reject(
                event,
                leave_id,
                reject_reason=str(reason) if reason is not None else None,
            )
            return _response(200, leave.to_dict())

        raise AppError(404, "NOT_FOUND", f"未知のルートです: {route}")

    except AppError as err:
        return _response(err.status_code, error_body(err.code, err.message, request_id))
    except Exception:
        return _response(
            500,
            error_body("INTERNAL_ERROR", "予期せぬエラーが発生しました", request_id),
        )
