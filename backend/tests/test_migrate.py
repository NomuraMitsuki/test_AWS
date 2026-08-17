"""migrate Lambda の単体テスト。DB はモック。Cognito は呼ばない。"""

from __future__ import annotations

from pathlib import Path

from lambda_loader import import_lambda

_handler_mod = import_lambda("migrate")
handler = _handler_mod.handler
apply_migrations = _handler_mod.apply_migrations
list_migration_files = _handler_mod.list_migration_files
migrations_dir = _handler_mod.migrations_dir

BACKEND = Path(__file__).resolve().parents[1]
REPO_MIGRATIONS = BACKEND / "migrations"


class FakeCursor:
    def __init__(self, conn: "FakeConn"):
        self.conn = conn

    def execute(self, sql, params=None):
        self.conn.executed.append((sql, params))
        if self.conn.execute_error is not None:
            err = self.conn.execute_error
            self.conn.execute_error = None
            raise err

    def fetchone(self):
        if self.conn.fetchone_queue:
            return self.conn.fetchone_queue.pop(0)
        return self.conn.fetchone_result

    def fetchall(self):
        return list(self.conn.fetchall_result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self):
        self.executed: list[tuple] = []
        self.fetchone_result = None
        self.fetchone_queue: list = []
        self.fetchall_result: list = []
        self.execute_error = None
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_list_migration_files_sorted_by_name():
    names = [p.name for p in list_migration_files(REPO_MIGRATIONS)]
    assert names == [
        "001_init_attendance.sql",
        "002_leave_requests.sql",
        "003_export_jobs.sql",
    ]


def test_empty_event_runs_migrate_in_filename_order():
    conn = FakeConn()
    result = handler({}, None, conn=conn)

    assert result["ok"] is True
    assert result["action"] == "migrate"
    assert result["applied"] == [
        "001_init_attendance.sql",
        "002_leave_requests.sql",
        "003_export_jobs.sql",
    ]
    assert conn.committed is True
    assert len(conn.executed) == 3
    assert "CREATE TABLE IF NOT EXISTS users" in conn.executed[0][0]
    assert "leave_requests" in conn.executed[1][0]
    assert "export_jobs" in conn.executed[2][0]


def test_action_migrate_is_explicit():
    conn = FakeConn()
    result = handler({"action": "migrate"}, None, conn=conn)
    assert result["ok"] is True
    assert result["applied"][0].startswith("001_")


def test_none_event_defaults_to_migrate():
    conn = FakeConn()
    result = handler(None, None, conn=conn)
    assert result["ok"] is True
    assert result["action"] == "migrate"


def test_seed_admin_inserts_admin_active():
    conn = FakeConn()
    conn.fetchall_result = []
    conn.fetchone_result = (
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "sub-admin-1",
        "admin@example.com",
        "Admin",
        "admin",
        "active",
    )

    result = handler(
        {
            "action": "seed_admin",
            "email": "admin@example.com",
            "cognito_sub": "sub-admin-1",
            "name": "Admin",
        },
        None,
        conn=conn,
    )

    assert result == {
        "ok": True,
        "action": "seed_admin",
        "created": True,
        "user": {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "cognito_sub": "sub-admin-1",
            "email": "admin@example.com",
            "name": "Admin",
            "role": "admin",
            "status": "active",
        },
    }
    insert_sql = conn.executed[1][0]
    insert_params = conn.executed[1][1]
    assert "INSERT INTO users" in insert_sql
    assert insert_params[1:] == ("sub-admin-1", "admin@example.com", "Admin")
    assert conn.committed is True


def test_seed_admin_duplicate_returns_existing():
    conn = FakeConn()
    conn.fetchall_result = [
        (
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "sub-admin-1",
            "admin@example.com",
            "Admin",
            "admin",
            "active",
        )
    ]

    result = handler(
        {
            "action": "seed_admin",
            "email": "admin@example.com",
            "cognito_sub": "sub-admin-1",
            "name": "Admin",
        },
        None,
        conn=conn,
    )

    assert result["ok"] is True
    assert result["created"] is False
    assert result["user"]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert not any("INSERT INTO users" in sql for sql, _ in conn.executed)


def test_seed_admin_conflict_when_email_and_sub_differ():
    conn = FakeConn()
    conn.fetchall_result = [
        (
            "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "other-sub",
            "admin@example.com",
            "Admin",
            "admin",
            "active",
        )
    ]

    result = handler(
        {
            "action": "seed_admin",
            "email": "admin@example.com",
            "cognito_sub": "sub-admin-1",
            "name": "Admin",
        },
        None,
        conn=conn,
    )

    assert result["ok"] is False
    assert result["code"] == "CONFLICT"


def test_seed_admin_missing_fields():
    conn = FakeConn()
    result = handler({"action": "seed_admin", "email": "a@example.com"}, None, conn=conn)
    assert result["ok"] is False
    assert result["code"] == "BAD_REQUEST"
    assert "cognito_sub" in result["error"]
    assert "name" in result["error"]
    assert conn.executed == []


def test_unknown_action():
    conn = FakeConn()
    result = handler({"action": "drop_all"}, None, conn=conn)
    assert result["ok"] is False
    assert result["code"] == "BAD_REQUEST"
    assert "drop_all" in result["error"]


def test_apply_migrations_override_dir(tmp_path: Path):
    (tmp_path / "002_later.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    conn = FakeConn()
    applied = apply_migrations(conn, tmp_path)
    assert applied == ["001_first.sql", "002_later.sql"]
    assert conn.executed[0][0] == "SELECT 1;"
    assert conn.executed[1][0] == "SELECT 2;"


def test_handler_does_not_call_cognito_apis():
    import inspect

    source = inspect.getsource(_handler_mod)
    assert "cognito-idp" not in source
    assert "admin_create_user" not in source
    assert "boto3.client(\"cognito" not in source
