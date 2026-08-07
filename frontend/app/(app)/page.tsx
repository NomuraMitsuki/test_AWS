"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type {
  AttendanceRecord,
  LeaveRequest,
  ListResponse,
} from "@/lib/api/types";
import { getRoles } from "@/lib/auth/session";
import { formatDateTime, todayLocalDate } from "@/lib/dates";

export default function DashboardPage() {
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [pendingCount, setPendingCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      const today = todayLocalDate();
      try {
        const roles = await getRoles();
        const attendance = await apiFetch<ListResponse<AttendanceRecord>>(
          `/attendance/records?scope=self&from=${today}&to=${today}`,
        );
        setTodayRecord(attendance.items[0] ?? null);

        if (roles.includes("manager") || roles.includes("admin")) {
          const scope = roles.includes("admin") ? "all" : "team";
          const leave = await apiFetch<ListResponse<LeaveRequest>>(
            `/leave-requests?scope=${scope}&status=pending`,
          );
          setPendingCount(leave.items.length);
        }
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const statusLabel = !todayRecord
    ? "未出勤"
    : todayRecord.clock_out_at
      ? "退勤済"
      : "出勤中";

  return (
    <section className="stack">
      <h1>ダッシュボード</h1>
      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading ? (
        <>
          <h2>本日の打刻（{todayLocalDate()}）</h2>
          <p>状態: {statusLabel}</p>
          <p>出勤: {formatDateTime(todayRecord?.clock_in_at)}</p>
          <p>退勤: {formatDateTime(todayRecord?.clock_out_at)}</p>
          <p>
            <Link href="/attendance">打刻画面へ</Link>
          </p>

          {pendingCount !== null ? (
            <>
              <h2>承認待ち休暇</h2>
              <p>
                {pendingCount} 件 —{" "}
                <Link href="/leave/approvals">承認画面へ</Link>
              </p>
            </>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
