"""エクスポート用リポジトリ境界。本番は RDS、テストはインメモリ。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass
class User:
    id: str
    cognito_sub: str
    email: str
    name: str
    role: str  # employee | manager | admin
    manager_id: Optional[str]
    status: str = "active"


@dataclass
class AttendanceRecord:
    id: str
    user_id: str
    work_date: date
    clock_in_at: datetime
    clock_out_at: Optional[datetime] = None
    note: Optional[str] = None


@dataclass
class ExportJob:
    id: str
    requested_by: str
    scope: str
    from_date: date
    to_date: date
    status: str = "pending"  # pending | completed | failed
    s3_key: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "requested_by": self.requested_by,
            "s3_key": self.s3_key,
            "status": self.status,
            "scope": self.scope,
            "from_date": self.from_date.isoformat(),
            "to_date": self.to_date.isoformat(),
            "created_at": _iso(self.created_at),
            "completed_at": _iso(self.completed_at) if self.completed_at else None,
        }


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


class ExportRepository(ABC):
    @abstractmethod
    def get_user_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def list_users_by_manager(self, manager_id: str) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def list_all_users(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def list_records(
        self,
        user_ids: list[str],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[AttendanceRecord]:
        raise NotImplementedError

    @abstractmethod
    def create_export_job(self, job: ExportJob) -> ExportJob:
        raise NotImplementedError

    @abstractmethod
    def update_export_job(self, job: ExportJob) -> ExportJob:
        raise NotImplementedError

    @abstractmethod
    def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        raise NotImplementedError


class InMemoryExportRepository(ExportRepository):
    """pytest 用インメモリ実装。"""

    def __init__(
        self,
        users: Optional[list[User]] = None,
        records: Optional[list[AttendanceRecord]] = None,
    ):
        self._users: dict[str, User] = {}
        self._by_sub: dict[str, str] = {}
        self._records: dict[tuple[str, date], AttendanceRecord] = {}
        self._jobs: dict[str, ExportJob] = {}
        for user in users or []:
            self.add_user(user)
        for rec in records or []:
            self.add_record(rec)

    def add_user(self, user: User) -> User:
        self._users[user.id] = user
        self._by_sub[user.cognito_sub] = user.id
        return user

    def add_record(self, record: AttendanceRecord) -> AttendanceRecord:
        self._records[(record.user_id, record.work_date)] = deepcopy(record)
        return deepcopy(record)

    def get_user_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        uid = self._by_sub.get(cognito_sub)
        return deepcopy(self._users[uid]) if uid else None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        user = self._users.get(user_id)
        return deepcopy(user) if user else None

    def list_users_by_manager(self, manager_id: str) -> list[User]:
        return [deepcopy(u) for u in self._users.values() if u.manager_id == manager_id]

    def list_all_users(self) -> list[User]:
        return [deepcopy(u) for u in self._users.values()]

    def list_records(
        self,
        user_ids: list[str],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[AttendanceRecord]:
        allowed = set(user_ids)
        items: list[AttendanceRecord] = []
        for (uid, work_date), rec in self._records.items():
            if uid not in allowed:
                continue
            if from_date and work_date < from_date:
                continue
            if to_date and work_date > to_date:
                continue
            items.append(deepcopy(rec))
        items.sort(key=lambda r: (r.work_date, r.user_id))
        return items

    def create_export_job(self, job: ExportJob) -> ExportJob:
        if not job.id:
            job.id = str(uuid4())
        now = datetime.now(timezone.utc)
        job.created_at = now
        self._jobs[job.id] = deepcopy(job)
        return deepcopy(job)

    def update_export_job(self, job: ExportJob) -> ExportJob:
        if job.id not in self._jobs:
            raise KeyError("export job not found")
        self._jobs[job.id] = deepcopy(job)
        return deepcopy(job)

    def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        job = self._jobs.get(job_id)
        return deepcopy(job) if job else None
