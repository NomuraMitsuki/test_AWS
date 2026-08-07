"""API Gateway HTTP API (payload 2.0) — 勤怠ルート。"""

from __future__ import annotations

import json
from datetime import date
from typing import Optional
from urllib.parse import parse_qs

from auth import request_id_from_event
from errors import AppError, error_body
from repository import AttendanceRepository, InMemoryAttendanceRepository
from service import AttendanceService

_default_repo: Optional[AttendanceRepository] = None


def get_repository() -> AttendanceRepository:
    global _default_repo
    if _default_repo is None:
        # 本番接続は後続で差し替え。単体テストは repo 引数で注入する。
        _default_repo = InMemoryAttendanceRepository()
    return _default_repo


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_date(value: Optional[str], field: str) -> Optional[date]:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppError(400, "BAD_REQUEST", f"{field} は YYYY-MM-DD 形式です") from exc


def _query_params(event: dict) -> dict:
    params = event.get("queryStringParameters") or {}
    if params:
        return params
    # フォールバック: rawQueryString
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


def handler(event, context, repo: Optional[AttendanceRepository] = None):
    request_id = request_id_from_event(event or {})
    repository = repo or get_repository()
    service = AttendanceService(repository)

    try:
        route = _route_key(event or {})
        qs = _query_params(event or {})

        if route == "POST /attendance/clock-in":
            record = service.clock_in(event)
            return _response(201, record.to_dict())

        if route == "POST /attendance/clock-out":
            record = service.clock_out(event)
            return _response(200, record.to_dict())

        if route == "GET /attendance/me":
            from_d = _parse_date(qs.get("from"), "from")
            to_d = _parse_date(qs.get("to"), "to")
            items = service.list_records(
                event, scope="self", from_date=from_d, to_date=to_d
            )
            return _response(200, {"items": [r.to_dict() for r in items]})

        if route == "GET /attendance/records":
            scope = qs.get("scope") or "self"
            from_d = _parse_date(qs.get("from"), "from")
            to_d = _parse_date(qs.get("to"), "to")
            user_id = qs.get("user_id") or None
            items = service.list_records(
                event,
                scope=scope,
                from_date=from_d,
                to_date=to_d,
                user_id=user_id,
            )
            return _response(200, {"items": [r.to_dict() for r in items]})

        if route == "GET /attendance/summary":
            year_raw = qs.get("year")
            month_raw = qs.get("month")
            if year_raw is None or month_raw is None or year_raw == "" or month_raw == "":
                raise AppError(400, "BAD_REQUEST", "year と month は必須です")
            try:
                year = int(year_raw)
                month = int(month_raw)
            except ValueError as exc:
                raise AppError(400, "BAD_REQUEST", "year / month は整数です") from exc
            if month < 1 or month > 12:
                raise AppError(400, "BAD_REQUEST", "month は 1〜12 です")
            user_id = qs.get("user_id") or None
            body = service.summary(event, year=year, month=month, user_id=user_id)
            return _response(200, body)

        raise AppError(404, "NOT_FOUND", f"未知のルートです: {route}")

    except AppError as err:
        return _response(err.status_code, error_body(err.code, err.message, request_id))
    except Exception:
        return _response(
            500,
            error_body("INTERNAL_ERROR", "予期せぬエラーが発生しました", request_id),
        )
