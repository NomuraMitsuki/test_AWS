"""エクスポート API（POST /exports/attendance）の単体テスト。"""

from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timezone

from lambda_loader import import_lambda

_handler_mod = import_lambda("exports")
handler = _handler_mod.handler

import repository  # noqa: E402
import storage  # noqa: E402

AttendanceRecord = repository.AttendanceRecord
ExportJob = repository.ExportJob
InMemoryExportRepository = repository.InMemoryExportRepository
User = repository.User
InMemoryStorageClient = storage.InMemoryStorageClient

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


def _records() -> list[AttendanceRecord]:
    return [
        AttendanceRecord(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            user_id=EMP_ID,
            work_date=date(2026, 8, 1),
            clock_in_at=datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc),
            clock_out_at=datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
            note="ok",
        ),
        AttendanceRecord(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            user_id=OTHER_ID,
            work_date=date(2026, 8, 1),
            clock_in_at=datetime(2026, 8, 1, 1, 0, tzinfo=timezone.utc),
            clock_out_at=None,
        ),
        AttendanceRecord(
            id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            user_id=EMP_ID,
            work_date=date(2026, 8, 5),
            clock_in_at=datetime(2026, 8, 5, 0, 30, tzinfo=timezone.utc),
            clock_out_at=datetime(2026, 8, 5, 8, 30, tzinfo=timezone.utc),
        ),
    ]


def _repo() -> InMemoryExportRepository:
    return InMemoryExportRepository(_users(), _records())


def _storage() -> InMemoryStorageClient:
    return InMemoryStorageClient()


def _event(
    sub: str,
    body: dict | None = None,
    email: str = "user@example.com",
    groups: str | list[str] | None = "employee",
    request_id: str = "req-test-1",
) -> dict:
    claims = {"sub": sub, "email": email}
    if groups is not None:
        claims["cognito:groups"] = groups
    event = {
        "version": "2.0",
        "routeKey": "POST /exports/attendance",
        "rawPath": "/exports/attendance",
        "requestContext": {
            "requestId": request_id,
            "http": {"method": "POST", "path": "/exports/attendance"},
            "authorizer": {"jwt": {"claims": claims}},
        },
    }
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def _body(response: dict) -> dict:
    return json.loads(response["body"])


def _csv_rows(csv_bytes: bytes) -> list[dict]:
    text = csv_bytes.decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def test_export_self_200_with_download_url():
    repo = _repo()
    storage = _storage()
    event = _event(
        EMP_SUB,
        body={"from_date": "2026-08-01", "to_date": "2026-08-31", "scope": "self"},
    )
    resp = handler(event, None, repo=repo, storage=storage)

    assert resp["statusCode"] == 200
    body = _body(resp)
    assert body["export_job_id"]
    assert body["download_url"].startswith("https://")
    assert body["expires_in"] == 300

    job = repo.get_export_job(body["export_job_id"])
    assert job is not None
    assert job.status == "completed"
    assert job.s3_key
    assert job.s3_key in storage.objects

    rows = _csv_rows(storage.objects[job.s3_key])
    assert len(rows) == 2
    assert all(r["user_id"] == EMP_ID for r in rows)
    assert rows[0]["email"] == "emp@example.com"


def test_export_employee_team_forbidden_403():
    repo = _repo()
    storage = _storage()
    event = _event(
        EMP_SUB,
        body={"from_date": "2026-08-01", "to_date": "2026-08-31", "scope": "team"},
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 403
    assert _body(resp)["code"] == "FORBIDDEN"


def test_export_manager_team_includes_reports_only():
    repo = _repo()
    storage = _storage()
    event = _event(
        MGR_SUB,
        body={"from_date": "2026-08-01", "to_date": "2026-08-31", "scope": "team"},
        groups="manager",
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 200
    job = repo.get_export_job(_body(resp)["export_job_id"])
    rows = _csv_rows(storage.objects[job.s3_key])
    assert {r["user_id"] for r in rows} == {EMP_ID}


def test_export_admin_all_includes_everyone():
    repo = _repo()
    storage = _storage()
    event = _event(
        ADM_SUB,
        body={"from_date": "2026-08-01", "to_date": "2026-08-31", "scope": "all"},
        groups="admin",
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 200
    job = repo.get_export_job(_body(resp)["export_job_id"])
    rows = _csv_rows(storage.objects[job.s3_key])
    assert {r["user_id"] for r in rows} == {EMP_ID, OTHER_ID}


def test_export_invalid_date_400():
    repo = _repo()
    storage = _storage()
    event = _event(
        EMP_SUB,
        body={"from_date": "not-a-date", "to_date": "2026-08-31", "scope": "self"},
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 400
    assert _body(resp)["code"] == "BAD_REQUEST"


def test_export_from_after_to_400():
    repo = _repo()
    storage = _storage()
    event = _event(
        EMP_SUB,
        body={"from_date": "2026-08-31", "to_date": "2026-08-01", "scope": "self"},
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 400
    assert _body(resp)["code"] == "BAD_REQUEST"


def test_export_unregistered_user_403():
    repo = _repo()
    storage = _storage()
    event = _event(
        "sub-unknown",
        body={"from_date": "2026-08-01", "to_date": "2026-08-31", "scope": "self"},
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 403
    assert _body(resp)["code"] == "FORBIDDEN"


def test_export_s3_failure_marks_job_failed():
    repo = _repo()
    storage = _storage()
    storage.fail_put = True
    event = _event(
        EMP_SUB,
        body={"from_date": "2026-08-01", "to_date": "2026-08-31", "scope": "self"},
    )
    resp = handler(event, None, repo=repo, storage=storage)
    assert resp["statusCode"] == 500
    jobs = list(repo._jobs.values())
    assert len(jobs) == 1
    assert jobs[0].status == "failed"
