"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { AttendanceSummary } from "@/lib/api/types";
import {
  currentYearMonth,
  formatDateTime,
  minutesToHoursLabel,
} from "@/lib/dates";

export default function AttendanceSummaryPage() {
  const searchParams = useSearchParams();
  const userId = searchParams.get("user_id");
  const initial = currentYearMonth();
  const [year, setYear] = useState(initial.year);
  const [month, setMonth] = useState(initial.month);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    async (y: number, m: number) => {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        year: String(y),
        month: String(m),
      });
      if (userId) params.set("user_id", userId);
      try {
        const data = await apiFetch<AttendanceSummary>(
          `/attendance/summary?${params.toString()}`,
        );
        setSummary(data);
      } catch (err) {
        setError(errorMessage(err));
        setSummary(null);
      } finally {
        setLoading(false);
      }
    },
    [userId],
  );

  useEffect(() => {
    void load(year, month);
  }, [load, year, month]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void load(year, month);
  }

  return (
    <section className="stack">
      <h1>月次サマリ</h1>
      <p>
        {userId
          ? `ユーザー ${userId} の月次勤務時間です。`
          : "本人の月次勤務時間です。"}
      </p>

      <form className="form" onSubmit={onSubmit}>
        <div className="row">
          <label>
            年
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              required
            />
          </label>
          <label>
            月
            <input
              type="number"
              min={1}
              max={12}
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              required
            />
          </label>
          <button className="btn" type="submit">
            表示
          </button>
        </div>
      </form>

      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {summary && !loading ? (
        <>
          <p>
            勤務日数: {summary.work_days} 日 ／ 合計:{" "}
            {minutesToHoursLabel(summary.total_work_minutes)}（
            {summary.total_work_minutes} 分）
          </p>
          <table className="table">
            <thead>
              <tr>
                <th>勤務日</th>
                <th>出勤</th>
                <th>退勤</th>
              </tr>
            </thead>
            <tbody>
              {summary.records.length === 0 ? (
                <tr>
                  <td colSpan={3}>レコードがありません</td>
                </tr>
              ) : (
                summary.records.map((row) => (
                  <tr key={row.id}>
                    <td>{row.work_date}</td>
                    <td>{formatDateTime(row.clock_in_at)}</td>
                    <td>{formatDateTime(row.clock_out_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </>
      ) : null}
    </section>
  );
}
