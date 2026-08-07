"""勤怠 CSV エクスポートのユースケース。"""

from __future__ import annotations

import csv
import io
import os
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from auth import get_cognito_sub, get_jwt_claims
from errors import AppError
from repository import AttendanceRecord, ExportJob, ExportRepository, User
from storage import StorageClient

DEFAULT_EXPIRES_IN = 300


def _iso(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def build_attendance_csv(records: list[AttendanceRecord], users_by_id: dict[str, User]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "user_id",
            "email",
            "name",
            "work_date",
            "clock_in_at",
            "clock_out_at",
            "note",
        ]
    )
    for rec in records:
        user = users_by_id.get(rec.user_id)
        writer.writerow(
            [
                rec.user_id,
                user.email if user else "",
                user.name if user else "",
                rec.work_date.isoformat(),
                _iso(rec.clock_in_at),
                _iso(rec.clock_out_at),
                rec.note or "",
            ]
        )
    return buf.getvalue()


class ExportService:
    def __init__(self, repo: ExportRepository, storage: StorageClient):
        self.repo = repo
        self.storage = storage
        self.expires_in = int(os.environ.get("PRESIGNED_URL_EXPIRES_IN", DEFAULT_EXPIRES_IN))

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

    def export_attendance(
        self,
        event: dict,
        from_date: date,
        to_date: date,
        scope: str,
    ) -> dict:
        if from_date > to_date:
            raise AppError(400, "BAD_REQUEST", "from_date は to_date 以前である必要があります")

        caller = self.resolve_caller(event)
        target_ids = self._resolve_scope_user_ids(caller, scope)

        job = ExportJob(
            id=str(uuid4()),
            requested_by=caller.id,
            scope=scope,
            from_date=from_date,
            to_date=to_date,
            status="pending",
        )
        job = self.repo.create_export_job(job)

        try:
            records = self.repo.list_records(target_ids, from_date=from_date, to_date=to_date)
            users_by_id = {u.id: u for u in self.repo.list_all_users()}
            csv_text = build_attendance_csv(records, users_by_id)
            s3_key = f"exports/{job.id}/attendance.csv"
            self.storage.put_object(s3_key, csv_text.encode("utf-8"), content_type="text/csv")
            download_url = self.storage.generate_presigned_url(s3_key, self.expires_in)

            job.status = "completed"
            job.s3_key = s3_key
            job.completed_at = datetime.now(timezone.utc)
            self.repo.update_export_job(job)

            return {
                "export_job_id": job.id,
                "download_url": download_url,
                "expires_in": self.expires_in,
            }
        except AppError:
            self._mark_failed(job)
            raise
        except Exception as exc:
            self._mark_failed(job)
            raise AppError(500, "INTERNAL_ERROR", "エクスポート処理に失敗しました") from exc

    def _mark_failed(self, job: ExportJob) -> None:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        try:
            self.repo.update_export_job(job)
        except Exception:
            pass

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
