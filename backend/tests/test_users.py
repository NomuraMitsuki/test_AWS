"""ユーザー API（list/invite/update）の単体テスト。"""

from __future__ import annotations

import json

from lambda_loader import import_lambda

_handler_mod = import_lambda("users")
handler = _handler_mod.handler

import cognito  # noqa: E402
import repository  # noqa: E402

InMemoryCognitoClient = cognito.InMemoryCognitoClient
InMemoryUserRepository = repository.InMemoryUserRepository
User = repository.User

EMP_ID = "11111111-1111-1111-1111-111111111111"
MGR_ID = "22222222-2222-2222-2222-222222222222"
ADM_ID = "33333333-3333-3333-3333-333333333333"

EMP_SUB = "sub-employee"
MGR_SUB = "sub-manager"
ADM_SUB = "sub-admin"


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
            id=ADM_ID,
            cognito_sub=ADM_SUB,
            email="admin@example.com",
            name="Admin",
            role="admin",
            manager_id=None,
        ),
    ]


def _repo() -> InMemoryUserRepository:
    return InMemoryUserRepository(_users())


def _cognito(repo: InMemoryUserRepository | None = None) -> InMemoryCognitoClient:
    client = InMemoryCognitoClient()
    source = repo or _repo()
    for u in source.list_users():
        client.users[u.cognito_sub] = {
            "email": u.email,
            "name": u.name,
            "groups": [u.role],
        }
        client.by_email[u.email] = u.cognito_sub
    return client


def _event(
    method: str,
    path: str,
    sub: str,
    email: str = "user@example.com",
    groups: str | list[str] | None = "admin",
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


def test_list_users_admin_200():
    repo = _repo()
    cognito_client = _cognito(repo)
    resp = handler(
        _event("GET", "/users", ADM_SUB),
        None,
        repo=repo,
        cognito=cognito_client,
    )
    assert resp["statusCode"] == 200
    items = _body(resp)["items"]
    assert len(items) == 3
    emails = {u["email"] for u in items}
    assert emails == {"emp@example.com", "mgr@example.com", "admin@example.com"}


def test_list_users_employee_403():
    repo = _repo()
    resp = handler(
        _event("GET", "/users", EMP_SUB, groups="employee"),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 403
    assert _body(resp)["code"] == "FORBIDDEN"


def test_list_users_manager_403():
    repo = _repo()
    resp = handler(
        _event("GET", "/users", MGR_SUB, groups="manager"),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 403


def test_invite_user_201():
    repo = _repo()
    cognito_client = _cognito(repo)
    resp = handler(
        _event(
            "POST",
            "/users",
            ADM_SUB,
            body={
                "email": "new@example.com",
                "name": "New User",
                "role": "employee",
                "manager_id": MGR_ID,
            },
        ),
        None,
        repo=repo,
        cognito=cognito_client,
    )
    assert resp["statusCode"] == 201, resp
    created = _body(resp)
    assert created["email"] == "new@example.com"
    assert created["name"] == "New User"
    assert created["role"] == "employee"
    assert created["manager_id"] == MGR_ID
    assert created["status"] == "active"
    assert created["id"]
    assert "new@example.com" in cognito_client.by_email


def test_invite_duplicate_email_409():
    repo = _repo()
    resp = handler(
        _event(
            "POST",
            "/users",
            ADM_SUB,
            body={
                "email": "emp@example.com",
                "name": "Dup",
                "role": "employee",
            },
        ),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 409
    assert _body(resp)["code"] == "CONFLICT"


def test_invite_non_admin_403():
    repo = _repo()
    resp = handler(
        _event(
            "POST",
            "/users",
            EMP_SUB,
            groups="employee",
            body={
                "email": "x@example.com",
                "name": "X",
                "role": "employee",
            },
        ),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 403


def test_invite_missing_fields_400():
    repo = _repo()
    resp = handler(
        _event("POST", "/users", ADM_SUB, body={"email": "a@example.com"}),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 400


def test_update_role_200():
    repo = _repo()
    cognito_client = _cognito(repo)
    resp = handler(
        _event(
            "PATCH",
            f"/users/{EMP_ID}",
            ADM_SUB,
            body={"role": "manager"},
            path_params={"id": EMP_ID},
            route_key="PATCH /users/{id}",
        ),
        None,
        repo=repo,
        cognito=cognito_client,
    )
    assert resp["statusCode"] == 200, resp
    updated = _body(resp)
    assert updated["role"] == "manager"
    assert cognito_client.users[EMP_SUB]["groups"] == ["manager"]


def test_update_manager_and_status_200():
    repo = _repo()
    resp = handler(
        _event(
            "PATCH",
            f"/users/{EMP_ID}",
            ADM_SUB,
            body={"manager_id": None, "status": "disabled"},
            path_params={"id": EMP_ID},
            route_key="PATCH /users/{id}",
        ),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 200
    updated = _body(resp)
    assert updated["manager_id"] is None
    assert updated["status"] == "disabled"


def test_update_missing_user_404():
    repo = _repo()
    missing = "99999999-9999-9999-9999-999999999999"
    resp = handler(
        _event(
            "PATCH",
            f"/users/{missing}",
            ADM_SUB,
            body={"status": "disabled"},
            path_params={"id": missing},
            route_key="PATCH /users/{id}",
        ),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 404
    assert _body(resp)["code"] == "NOT_FOUND"


def test_update_non_admin_403():
    repo = _repo()
    resp = handler(
        _event(
            "PATCH",
            f"/users/{EMP_ID}",
            MGR_SUB,
            groups="manager",
            body={"role": "admin"},
            path_params={"id": EMP_ID},
            route_key="PATCH /users/{id}",
        ),
        None,
        repo=repo,
        cognito=_cognito(repo),
    )
    assert resp["statusCode"] == 403


def test_unauthenticated_401():
    repo = _repo()
    event = {
        "version": "2.0",
        "routeKey": "GET /users",
        "rawPath": "/users",
        "requestContext": {
            "requestId": "req-no-auth",
            "http": {"method": "GET", "path": "/users"},
        },
    }
    resp = handler(event, None, repo=repo, cognito=_cognito(repo))
    assert resp["statusCode"] == 401
