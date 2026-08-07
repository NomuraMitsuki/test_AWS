"""ユーザーリポジトリ境界。本番は RDS、テストはインメモリ。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "manager_id": self.manager_id,
            "status": self.status,
        }


class UserRepository(ABC):
    @abstractmethod
    def get_user_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def list_users(self) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def create_user(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, user_id: str) -> None:
        raise NotImplementedError


class InMemoryUserRepository(UserRepository):
    """pytest 用インメモリ実装。"""

    def __init__(self, users: Optional[list[User]] = None):
        self._users: dict[str, User] = {}
        self._by_sub: dict[str, str] = {}
        self._by_email: dict[str, str] = {}
        for user in users or []:
            self.add_user(user)

    def add_user(self, user: User) -> User:
        if not user.id:
            user.id = str(uuid4())
        self._users[user.id] = user
        self._by_sub[user.cognito_sub] = user.id
        self._by_email[user.email.lower()] = user.id
        return user

    def get_user_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        uid = self._by_sub.get(cognito_sub)
        return deepcopy(self._users[uid]) if uid else None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        user = self._users.get(user_id)
        return deepcopy(user) if user else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        uid = self._by_email.get(email.lower())
        return deepcopy(self._users[uid]) if uid else None

    def list_users(self) -> list[User]:
        items = [deepcopy(u) for u in self._users.values()]
        items.sort(key=lambda u: (u.created_at, u.id))
        return items

    def create_user(self, user: User) -> User:
        if not user.id:
            user.id = str(uuid4())
        now = datetime.now(timezone.utc)
        user.created_at = now
        user.updated_at = now
        if user.email.lower() in self._by_email:
            raise KeyError("email already exists")
        self._users[user.id] = deepcopy(user)
        self._by_sub[user.cognito_sub] = user.id
        self._by_email[user.email.lower()] = user.id
        return deepcopy(user)

    def update_user(self, user: User) -> User:
        if user.id not in self._users:
            raise KeyError("user not found")
        old = self._users[user.id]
        if old.email.lower() != user.email.lower():
            self._by_email.pop(old.email.lower(), None)
            self._by_email[user.email.lower()] = user.id
        if old.cognito_sub != user.cognito_sub:
            self._by_sub.pop(old.cognito_sub, None)
            self._by_sub[user.cognito_sub] = user.id
        user.updated_at = datetime.now(timezone.utc)
        self._users[user.id] = deepcopy(user)
        return deepcopy(user)

    def delete_user(self, user_id: str) -> None:
        user = self._users.pop(user_id, None)
        if user:
            self._by_sub.pop(user.cognito_sub, None)
            self._by_email.pop(user.email.lower(), None)
