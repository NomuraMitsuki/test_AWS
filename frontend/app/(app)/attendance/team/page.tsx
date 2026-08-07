"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RequireRole } from "@/components/RequireRole";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { AttendanceRecord, ListResponse } from "@/lib/api/types";
import { getRoles } from "@/lib/auth/session";
import { formatDateTime } from "@/lib/dates";

function TeamAttendanceInner() {
  const [items, setItems] = useState<AttendanceRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [scopeLabel, setScopeLabel] = useState("team");

  useEffect(() => {
    void (async () => {
      try {
        const roles = await getRoles();
        const scope = roles.includes("admin") ? "all" : "team";
        setScopeLabel(scope);
        const data = await apiFetch<ListResponse<AttendanceRecord>>(
          `/attendance/records?scope=${scope}`,
        );
        setItems(data.items);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section className="stack">
      <h1>配下勤怠</h1>
      <p>scope={scopeLabel} の打刻履歴です。行から月次サマリへ遷移できます。</p>
      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error ? (
        <table className="table">
          <thead>
            <tr>
              <th>ユーザー</th>
              <th>勤務日</th>
              <th>出勤</th>
              <th>退勤</th>
              <th>サマリ</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5}>履歴がありません</td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id}>
                  <td>{row.user_id}</td>
                  <td>{row.work_date}</td>
                  <td>{formatDateTime(row.clock_in_at)}</td>
                  <td>{formatDateTime(row.clock_out_at)}</td>
                  <td>
                    <Link href={`/attendance/summary?user_id=${row.user_id}`}>
                      月次を見る
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}

export default function TeamAttendancePage() {
  return (
    <RequireRole roles={["manager", "admin"]}>
      <TeamAttendanceInner />
    </RequireRole>
  );
}
