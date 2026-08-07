"""休暇 API（list/create/approve/reject）の単体テスト。"""

from __future__ import annotations

import json

from lambda_loader import import_lambda

_handler_mod = import_lambda("leave")
handler = _handler_mod.handler

import repository  # noqa: E402  — lambda_loader が path をセットしたあと

InMemoryLeaveRepository = repository.InMemoryLeaveRepository
User = repository.User

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


def _repo() -> InMemoryLeaveRepository:
    return InMemoryLeaveRepository(_users())


def _event(
    method: str,
    path: str,
    sub: str,
    email: str = "user@example.com",
    groups: str | list[str] | None = "employee",
    query: dict | None = None,
    body: dict | None = None,
    path_params: dict | None = None,
    route_key: str | None = None,
    request_id: str = "req-test-1",
) -> dict:
    claims = {"sub": sub, "email": email}
    if groups is not None:
        claims["cognito:groups"] = groups
    event = {
        "version": "2.0",
        "routeKey": route_key or f"{method} {path}",
        "rawPath": path,
        "queryStringParameters": query,
        "pathParameters": path_params,
        "requestContext": {
            "requestId": request_id,
            "http": {"method": method, "path": path},
            "authorizer": {"jwt": {"claims": claims}},
        },
    }
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def _body(response: dict) -> dict:
    return json.loads(response["body"])


def _create(
    repo: InMemoryLeaveRepository,
    sub: str = EMP_SUB,
    leave_type: str = "paid",
    start: str = "2026-08-10",
    end: str = "2026-08-12",
    comment: str | None = "trip",
) -> dict:
    payload: dict = {
        "leave_type": leave_type,
        "start_date": start,
        "end_date": end,
    }
    if comment is not None:
        payload["comment"] = comment
    resp = handler(
        _event("POST", "/leave-requests", sub, body=payload),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 201, resp
    return _body(resp)


def test_create_leave_201_pending():
    repo = _repo()
    created = _create(repo)
    assert created["user_id"] == EMP_ID
    assert created["status"] == "pending"
    assert created["leave_type"] == "paid"
    assert created["start_date"] == "2026-08-10"
    assert created["end_date"] == "2026-08-12"
    assert created["comment"] == "trip"
    assert created["approver_id"] is None
    assert created["id"]


def test_create_invalid_dates_400():
    repo = _repo()
    resp = handler(
        _event(
            "POST",
            "/leave-requests",
            EMP_SUB,
            body={
                "leave_type": "paid",
                "start_date": "2026-08-15",
                "end_date": "2026-08-10",
            },
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 400
    assert _body(resp)["code"] == "BAD_REQUEST"


def test_create_invalid_leave_type_400():
    repo = _repo()
    resp = handler(
        _event(
            "POST",
            "/leave-requests",
            EMP_SUB,
            body={
                "leave_type": "vacation",
                "start_date": "2026-08-10",
                "end_date": "2026-08-11",
            },
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 400


def test_list_self_and_status_filter():
    repo = _repo()
    a = _create(repo, start="2026-08-10", end="2026-08-10")
    b = _create(repo, start="2026-08-20", end="2026-08-21")

    # approve one
    handler(
        _event(
            "POST",
            f"/leave-requests/{a['id']}/approve",
            MGR_SUB,
            groups="manager",
            path_params={"id": a["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )

    all_self = handler(
        _event("GET", "/leave-requests", EMP_SUB, query={"scope": "self"}),
        None,
        repo=repo,
    )
    assert all_self["statusCode"] == 200
    assert len(_body(all_self)["items"]) == 2

    pending = handler(
        _event(
            "GET",
            "/leave-requests",
            EMP_SUB,
            query={"scope": "self", "status": "pending"},
        ),
        None,
        repo=repo,
    )
    items = _body(pending)["items"]
    assert len(items) == 1
    assert items[0]["id"] == b["id"]


def test_list_team_manager_ok_employee_forbidden():
    repo = _repo()
    created = _create(repo)

    mgr = handler(
        _event(
            "GET",
            "/leave-requests",
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
    assert items[0]["id"] == created["id"]

    emp = handler(
        _event(
            "GET",
            "/leave-requests",
            EMP_SUB,
            query={"scope": "team"},
        ),
        None,
        repo=repo,
    )
    assert emp["statusCode"] == 403


def test_list_all_admin_only():
    repo = _repo()
    _create(repo, EMP_SUB)
    _create(repo, OTHER_SUB)

    admin = handler(
        _event(
            "GET",
            "/leave-requests",
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
            "/leave-requests",
            EMP_SUB,
            query={"scope": "all"},
        ),
        None,
        repo=repo,
    )
    assert emp["statusCode"] == 403


def test_approve_by_manager_200():
    repo = _repo()
    created = _create(repo)
    resp = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/approve",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["status"] == "approved"
    assert body["approver_id"] == MGR_ID


def test_approve_by_admin_200():
    repo = _repo()
    created = _create(repo, OTHER_SUB)
    resp = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/approve",
            ADM_SUB,
            groups="admin",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 200
    assert _body(resp)["status"] == "approved"


def test_approve_employee_forbidden_403():
    repo = _repo()
    created = _create(repo)
    resp = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/approve",
            EMP_SUB,
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 403


def test_approve_wrong_manager_403():
    repo = _repo()
    # OTHER は manager_id=None → MGR の配下ではない
    created = _create(repo, OTHER_SUB)
    resp = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/approve",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 403


def test_approve_not_pending_409():
    repo = _repo()
    created = _create(repo)
    ok = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/approve",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )
    assert ok["statusCode"] == 200

    again = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/approve",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/approve",
        ),
        None,
        repo=repo,
    )
    assert again["statusCode"] == 409
    assert _body(again)["code"] == "NOT_PENDING"


def test_reject_with_reason_200():
    repo = _repo()
    created = _create(repo)
    resp = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/reject",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/reject",
            body={"reject_reason": "busy season"},
        ),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["status"] == "rejected"
    assert body["reject_reason"] == "busy season"
    assert body["approver_id"] == MGR_ID


def test_reject_not_pending_409():
    repo = _repo()
    created = _create(repo)
    handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/reject",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/reject",
        ),
        None,
        repo=repo,
    )
    again = handler(
        _event(
            "POST",
            f"/leave-requests/{created['id']}/reject",
            MGR_SUB,
            groups="manager",
            path_params={"id": created["id"]},
            route_key="POST /leave-requests/{id}/reject",
        ),
        None,
        repo=repo,
    )
    assert again["statusCode"] == 409


def test_unauthorized_without_jwt_401():
    repo = _repo()
    event = {
        "version": "2.0",
        "routeKey": "GET /leave-requests",
        "rawPath": "/leave-requests",
        "requestContext": {
            "requestId": "req-no-auth",
            "http": {"method": "GET", "path": "/leave-requests"},
        },
    }
    resp = handler(event, None, repo=repo)
    assert resp["statusCode"] == 401
    assert _body(resp)["code"] == "UNAUTHORIZED"


def test_unknown_user_403():
    repo = _repo()
    resp = handler(
        _event("GET", "/leave-requests", "unknown-sub"),
        None,
        repo=repo,
    )
    assert resp["statusCode"] == 403
