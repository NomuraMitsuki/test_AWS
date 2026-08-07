"""休暇申請・承認／却下・一覧のユースケース。"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import uuid4

from auth import get_cognito_sub, get_jwt_claims
from errors import AppError
from repository import LeaveRepository, LeaveRequest, User

VALID_LEAVE_TYPES = frozenset({"paid", "absence", "other"})
VALID_STATUSES = frozenset({"pending", "approved", "rejected"})


class LeaveService:
    def __init__(self, repo: LeaveRepository):
        self.repo = repo

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

    def list_leaves(
        self,
        event: dict,
        scope: str = "self",
        status: Optional[str] = None,
    ) -> list[LeaveRequest]:
        caller = self.resolve_caller(event)
        if status is not None and status not in VALID_STATUSES:
            raise AppError(
                400, "BAD_REQUEST", "status は pending / approved / rejected のいずれかです"
            )
        target_ids = self._resolve_scope_user_ids(caller, scope)
        return self.repo.list_leaves(target_ids, status=status)

    def create_leave(
        self,
        event: dict,
        leave_type: str,
        start_date: date,
        end_date: date,
        comment: Optional[str] = None,
    ) -> LeaveRequest:
        caller = self.resolve_caller(event)
        if leave_type not in VALID_LEAVE_TYPES:
            raise AppError(
                400, "BAD_REQUEST", "leave_type は paid / absence / other のいずれかです"
            )
        if start_date > end_date:
            raise AppError(400, "BAD_REQUEST", "start_date は end_date 以前である必要があります")
        leave = LeaveRequest(
            id=str(uuid4()),
            user_id=caller.id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            comment=comment,
        )
        return self.repo.create_leave(leave)

    def approve(self, event: dict, leave_id: str) -> LeaveRequest:
        caller = self.resolve_caller(event)
        leave = self._get_leave_or_404(leave_id)
        self._assert_can_decide(caller, leave)
        if leave.status != "pending":
            raise AppError(409, "NOT_PENDING", "pending の申請のみ承認できます")
        leave.status = "approved"
        leave.approver_id = caller.id
        leave.reject_reason = None
        return self.repo.update_leave(leave)

    def reject(
        self,
        event: dict,
        leave_id: str,
        reject_reason: Optional[str] = None,
    ) -> LeaveRequest:
        caller = self.resolve_caller(event)
        leave = self._get_leave_or_404(leave_id)
        self._assert_can_decide(caller, leave)
        if leave.status != "pending":
            raise AppError(409, "NOT_PENDING", "pending の申請のみ却下できます")
        leave.status = "rejected"
        leave.approver_id = caller.id
        leave.reject_reason = reject_reason
        return self.repo.update_leave(leave)

    def _get_leave_or_404(self, leave_id: str) -> LeaveRequest:
        leave = self.repo.get_leave(leave_id)
        if not leave:
            raise AppError(404, "NOT_FOUND", "休暇申請が見つかりません")
        return leave

    def _assert_can_decide(self, caller: User, leave: LeaveRequest) -> None:
        if caller.role == "admin":
            return
        if caller.role == "manager":
            applicant = self.repo.get_user_by_id(leave.user_id)
            if applicant and applicant.manager_id == caller.id:
                return
            raise AppError(403, "FORBIDDEN", "配下以外の申請は承認／却下できません")
        raise AppError(403, "FORBIDDEN", "承認／却下の権限がありません")

    def _resolve_scope_user_ids(self, caller: User, scope: str) -> list[str]:
        if scope not in ("self", "team", "all"):
            raise AppError(400, "BAD_REQUEST", "scope は self / team / all のいずれかです")

        if scope == "self":
            if caller.role not in ("employee", "manager", "admin"):
                raise AppError(403, "FORBIDDEN", "権限がありません")
            return [caller.id]

        if scope == "team":
            if caller.role != "manager":
                raise AppError(403, "FORBIDDEN", "scope=team は manager のみ利用できます")
            reports = self.repo.list_users_by_manager(caller.id)
            return [u.id for u in reports]

        if caller.role != "admin":
            raise AppError(403, "FORBIDDEN", "scope=all は admin のみ利用できます")
        return [u.id for u in self.repo.list_all_users()]
