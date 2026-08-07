"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { AttendanceRecord, ListResponse } from "@/lib/api/types";
import { formatDateTime, todayLocalDate } from "@/lib/dates";

type ClockState = "not_in" | "in" | "out";

function deriveState(record: AttendanceRecord | null): ClockState {
  if (!record) return "not_in";
  if (record.clock_out_at) return "out";
  return "in";
}

export default function AttendanceClockPage() {
  const [record, setRecord] = useState<AttendanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const today = todayLocalDate();
    try {
      const data = await apiFetch<ListResponse<AttendanceRecord>>(
        `/attendance/records?scope=self&from=${today}&to=${today}`,
      );
      setRecord(data.items[0] ?? null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function clockIn() {
    setBusy(true);
    setError(null);
    try {
      const created = await apiFetch<AttendanceRecord>("/attendance/clock-in", {
        method: "POST",
      });
      setRecord(created);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function clockOut() {
    setBusy(true);
    setError(null);
    try {
      const updated = await apiFetch<AttendanceRecord>("/attendance/clock-out", {
        method: "POST",
      });
      setRecord(updated);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const state = deriveState(record);
  const stateLabel =
    state === "not_in" ? "未出勤" : state === "in" ? "出勤中" : "退勤済";

  return (
    <section className="stack">
      <h1>打刻</h1>
      <p>本日（{todayLocalDate()}）の出勤／退勤を登録します。</p>

      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {!loading ? (
        <>
          <p>
            状態: <strong>{stateLabel}</strong>
          </p>
          <p>出勤: {formatDateTime(record?.clock_in_at)}</p>
          <p>退勤: {formatDateTime(record?.clock_out_at)}</p>
          <div className="row">
            <button
              type="button"
              className="btn"
              disabled={busy || state !== "not_in"}
              onClick={() => void clockIn()}
            >
              出勤
            </button>
            <button
              type="button"
              className="btn"
              disabled={busy || state !== "in"}
              onClick={() => void clockOut()}
            >
              退勤
            </button>
          </div>
        </>
      ) : null}
    </section>
  );
}
