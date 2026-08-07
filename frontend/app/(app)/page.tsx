"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { AttendanceRecord, ListResponse } from "@/lib/api/types";
import { formatDateTime, todayLocalDate } from "@/lib/dates";

export default function DashboardPage() {
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      const today = todayLocalDate();
      try {
        const data = await apiFetch<ListResponse<AttendanceRecord>>(
          `/attendance/records?scope=self&from=${today}&to=${today}`,
        );
        setTodayRecord(data.items[0] ?? null);
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
        </>
      ) : null}
    </section>
  );
}
