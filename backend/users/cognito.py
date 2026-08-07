"""Cognito Admin API 境界。本番は boto3、テストはインメモリモック。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from errors import AppError

VALID_ROLES = frozenset({"employee", "manager", "admin"})


class CognitoClient(ABC):
    @abstractmethod
    def create_user(self, email: str, name: str, role: str) -> str:
        """ユーザーを作成し Cognito groups に追加。戻り値は cognito_sub。"""
        raise NotImplementedError

    @abstractmethod
    def set_user_groups(self, cognito_sub: str, role: str) -> None:
        """ロールに対応する単一グループへ同期する。"""
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, cognito_sub: str) -> None:
        """ロールバック用。存在しなくてもよい。"""
        raise NotImplementedError


class InMemoryCognitoClient(CognitoClient):
    """pytest 用モック。"""

    def __init__(self):
        self.users: dict[str, dict] = {}  # sub -> {email, name, groups}
        self.by_email: dict[str, str] = {}
        self.fail_create = False
        self.fail_set_groups = False

    def create_user(self, email: str, name: str, role: str) -> str:
        if role not in VALID_ROLES:
            raise AppError(400, "BAD_REQUEST", "role は employee / manager / admin のいずれかです")
        if self.fail_create:
            raise AppError(502, "COGNITO_ERROR", "Cognito ユーザー作成に失敗しました")
        if email in self.by_email:
            raise AppError(409, "CONFLICT", "このメールアドレスは既に登録されています")
        sub = f"sub-{uuid4()}"
        self.users[sub] = {"email": email, "name": name, "groups": [role]}
        self.by_email[email] = sub
        return sub

    def set_user_groups(self, cognito_sub: str, role: str) -> None:
        if role not in VALID_ROLES:
            raise AppError(400, "BAD_REQUEST", "role は employee / manager / admin のいずれかです")
        if self.fail_set_groups:
            raise AppError(502, "COGNITO_ERROR", "Cognito グループ同期に失敗しました")
        user = self.users.get(cognito_sub)
        if not user:
            raise AppError(404, "NOT_FOUND", "Cognito ユーザーが見つかりません")
        user["groups"] = [role]

    def delete_user(self, cognito_sub: str) -> None:
        user = self.users.pop(cognito_sub, None)
        if user:
            self.by_email.pop(user["email"], None)


class Boto3CognitoClient(CognitoClient):
    """本番用。USER_POOL_ID 環境変数必須。単体テストでは使わない。"""

    def __init__(self, user_pool_id: str, client=None):
        self.user_pool_id = user_pool_id
        if client is not None:
            self._client = client
        else:
            import boto3

            self._client = boto3.client("cognito-idp")

    def create_user(self, email: str, name: str, role: str) -> str:
        if role not in VALID_ROLES:
            raise AppError(400, "BAD_REQUEST", "role は employee / manager / admin のいずれかです")
        try:
            resp = self._client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                    {"Name": "name", "Value": name},
                ],
                DesiredDeliveryMediums=["EMAIL"],
            )
            attrs = {a["Name"]: a["Value"] for a in resp["User"]["Attributes"]}
            sub = attrs["sub"]
            self._client.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=email,
                GroupName=role,
            )
            return sub
        except self._client.exceptions.UsernameExistsException as exc:
            raise AppError(409, "CONFLICT", "このメールアドレスは既に登録されています") from exc
        except Exception as exc:
            raise AppError(502, "COGNITO_ERROR", "Cognito ユーザー作成に失敗しました") from exc

    def set_user_groups(self, cognito_sub: str, role: str) -> None:
        if role not in VALID_ROLES:
            raise AppError(400, "BAD_REQUEST", "role は employee / manager / admin のいずれかです")
        try:
            user = self._client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=cognito_sub,
            )
            username = user["Username"]
            groups = self._client.admin_list_groups_for_user(
                UserPoolId=self.user_pool_id,
                Username=username,
            )
            for g in groups.get("Groups", []):
                name = g["GroupName"]
                if name in VALID_ROLES and name != role:
                    self._client.admin_remove_user_from_group(
                        UserPoolId=self.user_pool_id,
                        Username=username,
                        GroupName=name,
                    )
            current = {g["GroupName"] for g in groups.get("Groups", [])}
            if role not in current:
                self._client.admin_add_user_to_group(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    GroupName=role,
                )
        except Exception as exc:
            raise AppError(502, "COGNITO_ERROR", "Cognito グループ同期に失敗しました") from exc

    def delete_user(self, cognito_sub: str) -> None:
        try:
            self._client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=cognito_sub,
            )
        except Exception:
            pass


def default_cognito_client() -> CognitoClient:
    import os

    pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    if pool_id:
        return Boto3CognitoClient(pool_id)
    return InMemoryCognitoClient()
