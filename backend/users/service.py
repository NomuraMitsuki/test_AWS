"""ユーザー一覧・招待・更新のユースケース。"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from auth import get_cognito_sub, get_jwt_claims
from cognito import CognitoClient, VALID_ROLES
from errors import AppError
from repository import User, UserRepository

VALID_STATUSES = frozenset({"active", "disabled"})


class UserService:
    def __init__(self, repo: UserRepository, cognito: CognitoClient):
        self.repo = repo
        self.cognito = cognito

    def resolve_caller(self, event: dict) -> User:
        claims = get_jwt_claims(event)
        if not claims:
            raise AppError(401, "UNAUTHORIZED", "認証が必要です")
        sub = get_cognito_sub(claims)
        if not sub:
            raise AppError(401, "UNAUTHORIZED", "JWT に sub がありません")
        user = self.repo.get_user_by_cognito_sub(sub)
        if not user or user.status != "active":
            raise AppError(403, "FORBIDDEN", "アプリユーザーが見つからないか無効です")
        return user

    def _require_admin(self, event: dict) -> User:
        caller = self.resolve_caller(event)
        if caller.role != "admin":
            raise AppError(403, "FORBIDDEN", "admin のみ利用できます")
        return caller

    def list_users(self, event: dict) -> list[User]:
        self._require_admin(event)
        return self.repo.list_users()

    def invite_user(
        self,
        event: dict,
        email: str,
        name: str,
        role: str,
        manager_id: Optional[str] = None,
    ) -> User:
        self._require_admin(event)
        email = email.strip()
        name = name.strip()
        if not email:
            raise AppError(400, "BAD_REQUEST", "email は必須です")
        if not name:
            raise AppError(400, "BAD_REQUEST", "name は必須です")
        if role not in VALID_ROLES:
            raise AppError(
                400, "BAD_REQUEST", "role は employee / manager / admin のいずれかです"
            )
        if self.repo.get_user_by_email(email):
            raise AppError(409, "CONFLICT", "このメールアドレスは既に登録されています")
        if manager_id is not None:
            manager = self.repo.get_user_by_id(manager_id)
            if not manager:
                raise AppError(400, "BAD_REQUEST", "manager_id が不正です")

        cognito_sub = self.cognito.create_user(email=email, name=name, role=role)
        user = User(
            id=str(uuid4()),
            cognito_sub=cognito_sub,
            email=email,
            name=name,
            role=role,
            manager_id=manager_id,
            status="active",
        )
        try:
            return self.repo.create_user(user)
        except Exception:
            # DB 失敗時は Cognito 側を可能な範囲でロールバック
            self.cognito.delete_user(cognito_sub)
            raise

    def update_user(
        self,
        event: dict,
        user_id: str,
        *,
        name: Optional[str] = None,
        role: Optional[str] = None,
        manager_id: object = ...,
        status: Optional[str] = None,
    ) -> User:
        self._require_admin(event)
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise AppError(404, "NOT_FOUND", "ユーザーが見つかりません")

        if name is not None:
            name = name.strip()
            if not name:
                raise AppError(400, "BAD_REQUEST", "name は空にできません")
            user.name = name

        if role is not None:
            if role not in VALID_ROLES:
                raise AppError(
                    400, "BAD_REQUEST", "role は employee / manager / admin のいずれかです"
                )
            if role != user.role:
                self.cognito.set_user_groups(user.cognito_sub, role)
                user.role = role

        if manager_id is not ...:
            if manager_id is not None:
                manager_id_str = str(manager_id)
                if manager_id_str == user.id:
                    raise AppError(400, "BAD_REQUEST", "自分自身を上長にはできません")
                manager = self.repo.get_user_by_id(manager_id_str)
                if not manager:
                    raise AppError(400, "BAD_REQUEST", "manager_id が不正です")
                user.manager_id = manager_id_str
            else:
                user.manager_id = None

        if status is not None:
            if status not in VALID_STATUSES:
                raise AppError(400, "BAD_REQUEST", "status は active / disabled のいずれかです")
            user.status = status

        return self.repo.update_user(user)
