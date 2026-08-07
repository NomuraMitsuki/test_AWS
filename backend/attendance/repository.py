"""勤怠リポジトリ境界。本番は RDS、テストはインメモリ。"""

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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "work_date": self.work_date.isoformat(),
            "clock_in_at": _iso(self.clock_in_at),
            "clock_out_at": _iso(self.clock_out_at) if self.clock_out_at else None,
            "note": self.note,
        }


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


class AttendanceRepository(ABC):
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
    def get_record(self, user_id: str, work_date: date) -> Optional[AttendanceRecord]:
        raise NotImplementedError

    @abstractmethod
    def create_record(self, record: AttendanceRecord) -> AttendanceRecord:
        raise NotImplementedError

    @abstractmethod
    def update_record(self, record: AttendanceRecord) -> AttendanceRecord:
        raise NotImplementedError

    @abstractmethod
    def list_records(
        self,
        user_ids: list[str],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[AttendanceRecord]:
        raise NotImplementedError


class InMemoryAttendanceRepository(AttendanceRepository):
    """pytest 用インメモリ実装。"""

    def __init__(self, users: Optional[list[User]] = None):
        self._users: dict[str, User] = {}
        self._by_sub: dict[str, str] = {}
        self._records: dict[tuple[str, date], AttendanceRecord] = {}
        for user in users or []:
            self.add_user(user)

    def add_user(self, user: User) -> User:
        self._users[user.id] = user
        self._by_sub[user.cognito_sub] = user.id
        return user

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

    def get_record(self, user_id: str, work_date: date) -> Optional[AttendanceRecord]:
        rec = self._records.get((user_id, work_date))
        return deepcopy(rec) if rec else None

    def create_record(self, record: AttendanceRecord) -> AttendanceRecord:
        key = (record.user_id, record.work_date)
        if key in self._records:
            raise ValueError("duplicate attendance record")
        if not record.id:
            record.id = str(uuid4())
        now = datetime.now(timezone.utc)
        record.created_at = now
        record.updated_at = now
        self._records[key] = deepcopy(record)
        return deepcopy(record)

    def update_record(self, record: AttendanceRecord) -> AttendanceRecord:
        key = (record.user_id, record.work_date)
        if key not in self._records:
            raise KeyError("attendance record not found")
        record.updated_at = datetime.now(timezone.utc)
        self._records[key] = deepcopy(record)
        return deepcopy(record)

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
        items.sort(key=lambda r: (r.work_date, r.user_id), reverse=True)
        return items
