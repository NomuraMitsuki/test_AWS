"""勤怠 API（clock-in/out, records, me, summary）の単体テスト。"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from lambda_loader import import_lambda

_handler_mod = import_lambda("attendance")
handler = _handler_mod.handler

import repository  # noqa: E402  — lambda_loader が path をセットしたあと
import service  # noqa: E402

InMemoryAttendanceRepository = repository.InMemoryAttendanceRepository
User = repository.User
today_jst = service.today_jst
AttendanceService = service.AttendanceService

EMP_ID = "11111111-1111-1111-1111-111111111111"
MGR_ID = "22222222-2222-2222-2222-222222222222"
ADM_ID = "33333333-3333-3333-3333-333333333333"
OTHER_ID = "44444444-4444-4444-4444-444444444444"

EMP_SUB = "sub-employee"
MGR_SUB = "sub-manager"
ADM_SUB = "sub-admin"
OTHER_SUB = "sub-other"


def _users() -> list[User]:
    return [
        User(
            id=MGR_ID,
            cognito_sub=MGR_SUB,
            email="mgr@example.com",
            name="Manager",
            role="manager",
            manager_id=None,
        ),
        User(
            id=EMP_ID,
            cognito_sub=EMP_SUB,
            email="emp@example.com",
            name="Employee",
            role="employee",
            manager_id=MGR_ID,
        ),
        User(
            id=OTHER_ID,
            cognito_sub=OTHER_SUB,
            email="other@example.com",
            name="Other",
            role="employee",
            manager_id=None,
        ),
        User(
            id=ADM_ID,
            cognito_sub=ADM_SUB,
            email="admin@example.com",
            name="Admin",
            role="admin",
            manager_id=None,
        ),
    ]


def _repo() -> InMemoryAttendanceRepository:
    return InMemoryAttendanceRepository(_users())


def _event(
    method: str,
    path: str,
    sub: str,
    email: str = "user@example.com",
    groups: str | list[str] | None = "employee",
    query: dict | None = None,
    request_id: str = "req-test-1",
) -> dict:
    claims = {"sub": sub, "email": email}
    if groups is not None:
        claims["cognito:groups"] = groups
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "queryStringParameters": query,
        "requestContext": {
            "requestId": request_id,
            "http": {"method": method, "path": path},
            "authorizer": {"jwt": {"claims": claims}},
        },
    }


def _body(response: dict) -> dict:
    return json.loads(response["body"])


def test_clock_in_creates_record_201():
    repo = _repo()
    event = _event("POST", "/attendance/clock-in", EMP_SUB)
    resp = handler(event, None, repo=repo)

    assert resp["statusCode"] == 201
    body = _body(resp)
    assert body["user_id"] == EMP_ID
    assert body["work_date"] == today_jst().isoformat()
    assert body["clock_in_at"]
    assert body["clock_out_at"] is None


def test_clock_in_duplicate_409():
    repo = _repo()
    event = _event("POST", "/attendance/clock-in", EMP_SUB)
    assert handler(event, None, repo=repo)["statusCode"] == 201

    resp = handler(event, None, repo=repo)
    assert resp["statusCode"] == 409
    body = _body(resp)
    assert body["code"] == "ALREADY_CLOCKED_IN"
    assert body["request_id"] == "req-test-1"


def test_clock_out_success_200():
    repo = _repo()
    handler(_event("POST", "/attendance/clock-in", EMP_SUB), None, repo=repo)
    resp = handler(_event("POST", "/attendance/clock-out", EMP_SUB), None, repo=repo)

    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["clock_out_at"] is not None


def test_clock_out_without_clock_in_409():
    repo = _repo()
    resp = handler(_event("POST", "/attendance/clock-out", EMP_SUB), None, repo=repo)
    assert resp["statusCode"] == 409
    assert _body(resp)["code"] == "NOT_CLOCKED_IN"


def test_clock_out_already_out_409():
    repo = _repo()
    handler(_event("POST", "/attendance/clock-in", EMP_SUB), None, repo=repo)
    handler(_event("POST", "/attendance/clock-out", EMP_SUB), None, repo=repo)
    resp = handler(_event("POST", "/attendance/clock-out", EMP_SUB), None, repo=repo)
    assert resp["statusCode"] == 409
    assert _body(resp)["code"] == "ALREADY_CLOCKED_OUT"


def test_records_self_and_me_alias():
    repo = _repo()
    handler(_event("POST", "/attendance/clock-in", EMP_SUB), None, repo=repo)

    records = handler(
        _event("GET", "/attendance/records", EMP_SUB, query={"scope": "self"}),
        None,
        repo=repo,
    )
    me = handler(_event("GET", "/attendance/me", EMP_SUB), None, repo=repo)

    assert records["statusCode"] == 200
    assert me["statusCode"] == 200
    assert _body(records)["items"] == _body(me)["items"]
    assert len(_body(records)["items"]) == 1


def test_records_team_manager_ok_employee_forbidden():
    repo = _repo()
    handler(_event("POST", "/attendance/clock-in", EMP_SUB), None, repo=repo)

    mgr = handler(
        _event(
            "GET",
            "/attendance/records",
            MGR_SUB,
            groups="manager",
            query={"scope": "team"},
        ),
        None,
        repo=repo,
    )
    assert mgr["statusCode"] == 200
    items = _body(mgr)["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == EMP_ID

    emp = handler(
        _event(
            "GET",
            "/attendance/records",
            EMP_SUB,
            query={"scope": "team"},
        ),
        None,
        repo=repo,
    )
    assert emp["statusCode"] == 403
    assert _body(emp)["code"] == "FORBIDDEN"


def test_records_all_admin_only():
    repo = _repo()
    handler(_event("POST", "/attendance/clock-in", EMP_SUB), None, repo=repo)
    handler(_event("POST", "/attendance/clock-in", OTHER_SUB), None, repo=repo)

    admin = handler(
        _event(
            "GET",
            "/attendance/records",
            ADM_SUB,
            groups="admin",
            query={"scope": "all"},
        ),
        None,
        repo=repo,
    )
    assert admin["statusCode"] == 200
    assert len(_body(admin)["items"]) == 2

    emp = handler(
        _event(
            "GET",
            "/attendance/records",
            EMP_SUB,
            query={"scope": "all"},
        ),
        None,
        repo=repo,
    )
    assert emp["statusCode"] == 403


def test_summary_self_and_work_minutes():
    repo = _repo()
    # 固定時刻で打刻（JST 当日）
    now_in = datetime(2026, 8, 7, 0, 0, 0, tzinfo=timezone.utc)  # JST 09:00
    now_out = datetime(2026, 8, 7, 8, 0, 0, tzinfo=timezone.utc)  # JST 17:00

    svc = AttendanceService(repo)
    event = _event("POST", "/attendance/clock-in", EMP_SUB)
    svc.clock_in(event, now=now_in)
    svc.clock_out(event, now=now_out)

    resp = handler(
        _event(
            "GET",
            "/attendance/summary",
            EMP_SUB,
            query={"year": "2026", "month": "8"},
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["year"] == 2026
    assert body["month"] == 8
    assert body["work_days"] == 1
    assert body["total_work_minutes"] == 480
    assert len(body["records"]) == 1


def test_summary_manager_report_ok_other_forbidden():
    repo = _repo()
    handler(_event("POST", "/attendance/clock-in", EMP_SUB), None, repo=repo)

    ok = handler(
        _event(
            "GET",
            "/attendance/summary",
            MGR_SUB,
            groups="manager",
            query={
                "year": str(today_jst().year),
                "month": str(today_jst().month),
                "user_id": EMP_ID,
            },
        ),
        None,
        repo=repo,
    )
    assert ok["statusCode"] == 200

    forbidden = handler(
        _event(
            "GET",
            "/attendance/summary",
            MGR_SUB,
            groups="manager",
            query={
                "year": str(today_jst().year),
                "month": str(today_jst().month),
                "user_id": OTHER_ID,
            },
        ),
        None,
        repo=repo,
    )
    assert forbidden["statusCode"] == 403


def test_summary_missing_year_month_400():
    repo = _repo()
    resp = handler(
        _event("GET", "/attendance/summary", EMP_SUB, query={}),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 400
    assert _body(resp)["code"] == "BAD_REQUEST"


def test_unauthorized_without_jwt_401():
    repo = _repo()
    event = {
        "version": "2.0",
        "routeKey": "POST /attendance/clock-in",
        "rawPath": "/attendance/clock-in",
        "requestContext": {
            "requestId": "req-no-auth",
            "http": {"method": "POST", "path": "/attendance/clock-in"},
        },
    }
    resp = handler(event, None, repo=repo)
    assert resp["statusCode"] == 401
    assert _body(resp)["code"] == "UNAUTHORIZED"


def test_unknown_user_403():
    repo = _repo()
    resp = handler(
        _event("POST", "/attendance/clock-in", "unknown-sub"),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 403


def test_today_jst_boundary():
    # UTC 2026-08-06 15:00 → JST 2026-08-07 00:00
    assert today_jst(datetime(2026, 8, 6, 15, 0, 0, tzinfo=timezone.utc)) == date(
        2026, 8, 7
    )
    # UTC 2026-08-06 14:59 → JST 2026-08-06 23:59
    assert today_jst(datetime(2026, 8, 6, 14, 59, 0, tzinfo=timezone.utc)) == date(
        2026, 8, 6
    )
