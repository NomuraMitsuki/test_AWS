"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { AttendanceRecord, ListResponse } from "@/lib/api/types";
import { formatDateTime } from "@/lib/dates";

export default function AttendanceHistoryPage() {
  const [items, setItems] = useState<AttendanceRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const data = await apiFetch<ListResponse<AttendanceRecord>>(
          "/attendance/records?scope=self",
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
      <h1>打刻履歴</h1>
      <p>
        本人の打刻履歴です。月次は{" "}
        <Link href="/attendance/summary">サマリ</Link> を参照。
      </p>
      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error ? (
        <table className="table">
          <thead>
            <tr>
              <th>勤務日</th>
              <th>出勤</th>
              <th>退勤</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={3}>履歴がありません</td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id}>
                  <td>{row.work_date}</td>
                  <td>{formatDateTime(row.clock_in_at)}</td>
                  <td>{formatDateTime(row.clock_out_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
