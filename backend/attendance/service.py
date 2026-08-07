"""打刻・履歴・サマリのユースケース。"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from auth import get_cognito_sub, get_jwt_claims
from errors import AppError
from repository import AttendanceRecord, AttendanceRepository, User

JST = ZoneInfo("Asia/Tokyo")


def today_jst(now: Optional[datetime] = None) -> date:
    dt = now or datetime.now(timezone.utc)
    return dt.astimezone(JST).date()


class AttendanceService:
    def __init__(self, repo: AttendanceRepository):
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

    def clock_in(self, event: dict, now: Optional[datetime] = None) -> AttendanceRecord:
        user = self.resolve_caller(event)
        work_date = today_jst(now)
        existing = self.repo.get_record(user.id, work_date)
        if existing is not None:
            raise AppError(409, "ALREADY_CLOCKED_IN", "本日は既に出勤打刻済みです")
        ts = now or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        record = AttendanceRecord(
            id=str(uuid4()),
            user_id=user.id,
            work_date=work_date,
            clock_in_at=ts,
        )
        return self.repo.create_record(record)

    def clock_out(self, event: dict, now: Optional[datetime] = None) -> AttendanceRecord:
        user = self.resolve_caller(event)
        work_date = today_jst(now)
        existing = self.repo.get_record(user.id, work_date)
        if existing is None:
            raise AppError(409, "NOT_CLOCKED_IN", "本日はまだ出勤打刻がありません")
        if existing.clock_out_at is not None:
            raise AppError(409, "ALREADY_CLOCKED_OUT", "本日は既に退勤打刻済みです")
        ts = now or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        existing.clock_out_at = ts
        return self.repo.update_record(existing)

    def list_records(
        self,
        event: dict,
        scope: str = "self",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        user_id: Optional[str] = None,
    ) -> list[AttendanceRecord]:
        caller = self.resolve_caller(event)
        target_ids = self._resolve_scope_user_ids(caller, scope, user_id)
        return self.repo.list_records(target_ids, from_date=from_date, to_date=to_date)

    def summary(
        self,
        event: dict,
        year: int,
        month: int,
        user_id: Optional[str] = None,
    ) -> dict:
        caller = self.resolve_caller(event)
        target = self._resolve_summary_user(caller, user_id)
        first = date(year, month, 1)
        last = date(year, month, monthrange(year, month)[1])
        records = self.repo.list_records([target.id], from_date=first, to_date=last)
        # work_date 昇順で返す
        records.sort(key=lambda r: r.work_date)
        total_minutes = 0
        work_days = 0
        for rec in records:
            work_days += 1
            if rec.clock_out_at is not None:
                delta = rec.clock_out_at - rec.clock_in_at
                total_minutes += max(0, int(delta.total_seconds() // 60))
        return {
            "year": year,
            "month": month,
            "total_work_minutes": total_minutes,
            "work_days": work_days,
            "records": [r.to_dict() for r in records],
        }

    def _resolve_scope_user_ids(
        self,
        caller: User,
        scope: str,
        user_id: Optional[str],
    ) -> list[str]:
        if scope not in ("self", "team", "all"):
            raise AppError(400, "BAD_REQUEST", "scope は self / team / all のいずれかです")

        if scope == "self":
            if caller.role not in ("employee", "manager", "admin"):
                raise AppError(403, "FORBIDDEN", "権限がありません")
            if user_id and user_id != caller.id:
                raise AppError(403, "FORBIDDEN", "scope=self では他ユーザーを指定できません")
            return [caller.id]

        if scope == "team":
            if caller.role != "manager":
                raise AppError(403, "FORBIDDEN", "scope=team は manager のみ利用できます")
            reports = self.repo.list_users_by_manager(caller.id)
            allowed = {u.id for u in reports}
            if user_id:
                if user_id not in allowed:
                    raise AppError(403, "FORBIDDEN", "指定ユーザーは配下にいません")
                return [user_id]
            return list(allowed)

        # scope == all
        if caller.role != "admin":
            raise AppError(403, "FORBIDDEN", "scope=all は admin のみ利用できます")
        if user_id:
            target = self.repo.get_user_by_id(user_id)
            if not target:
                raise AppError(403, "FORBIDDEN", "指定ユーザーが見つかりません")
            return [user_id]
        return [u.id for u in self.repo.list_all_users()]

    def _resolve_summary_user(self, caller: User, user_id: Optional[str]) -> User:
        if not user_id or user_id == caller.id:
            return caller
        target = self.repo.get_user_by_id(user_id)
        if not target:
            raise AppError(403, "FORBIDDEN", "指定ユーザーが見つかりません")
        if caller.role == "admin":
            return target
        if caller.role == "manager" and target.manager_id == caller.id:
            return target
        raise AppError(403, "FORBIDDEN", "他者サマリを閲覧する権限がありません")
