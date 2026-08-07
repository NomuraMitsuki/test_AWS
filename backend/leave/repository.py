"""休暇リポジトリ境界。本番は RDS、テストはインメモリ。"""

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
class LeaveRequest:
    id: str
    user_id: str
    leave_type: str  # paid | absence | other
    start_date: date
    end_date: date
    status: str  # pending | approved | rejected
    approver_id: Optional[str] = None
    comment: Optional[str] = None
    reject_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "approver_id": self.approver_id,
            "comment": self.comment,
            "reject_reason": self.reject_reason,
            "created_at": _iso(self.created_at),
        }


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


class LeaveRepository(ABC):
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
    def create_leave(self, leave: LeaveRequest) -> LeaveRequest:
        raise NotImplementedError

    @abstractmethod
    def get_leave(self, leave_id: str) -> Optional[LeaveRequest]:
        raise NotImplementedError

    @abstractmethod
    def update_leave(self, leave: LeaveRequest) -> LeaveRequest:
        raise NotImplementedError

    @abstractmethod
    def list_leaves(
        self,
        user_ids: list[str],
        status: Optional[str] = None,
    ) -> list[LeaveRequest]:
        raise NotImplementedError


class InMemoryLeaveRepository(LeaveRepository):
    """pytest 用インメモリ実装。"""

    def __init__(self, users: Optional[list[User]] = None):
        self._users: dict[str, User] = {}
        self._by_sub: dict[str, str] = {}
        self._leaves: dict[str, LeaveRequest] = {}
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

    def create_leave(self, leave: LeaveRequest) -> LeaveRequest:
        if not leave.id:
            leave.id = str(uuid4())
        now = datetime.now(timezone.utc)
        leave.created_at = now
        leave.updated_at = now
        self._leaves[leave.id] = deepcopy(leave)
        return deepcopy(leave)

    def get_leave(self, leave_id: str) -> Optional[LeaveRequest]:
        leave = self._leaves.get(leave_id)
        return deepcopy(leave) if leave else None

    def update_leave(self, leave: LeaveRequest) -> LeaveRequest:
        if leave.id not in self._leaves:
            raise KeyError("leave request not found")
        leave.updated_at = datetime.now(timezone.utc)
        self._leaves[leave.id] = deepcopy(leave)
        return deepcopy(leave)

    def list_leaves(
        self,
        user_ids: list[str],
        status: Optional[str] = None,
    ) -> list[LeaveRequest]:
        allowed = set(user_ids)
        items: list[LeaveRequest] = []
        for leave in self._leaves.values():
            if leave.user_id not in allowed:
                continue
            if status and leave.status != status:
                continue
            items.append(deepcopy(leave))
        items.sort(key=lambda r: (r.created_at, r.id), reverse=True)
        return items
