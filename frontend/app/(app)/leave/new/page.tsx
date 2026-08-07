"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { LeaveRequest, LeaveType } from "@/lib/api/types";

export default function LeaveNewPage() {
  const router = useRouter();
  const [leaveType, setLeaveType] = useState<LeaveType>("paid");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch<LeaveRequest>("/leave-requests", {
        method: "POST",
        body: JSON.stringify({
          leave_type: leaveType,
          start_date: startDate,
          end_date: endDate,
          comment: comment.trim() || undefined,
        }),
      });
      router.push("/leave");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="stack">
      <h1>休暇申請作成</h1>
      <form className="form" onSubmit={onSubmit}>
        <label>
          種別
          <select
            value={leaveType}
            onChange={(e) => setLeaveType(e.target.value as LeaveType)}
          >
            <option value="paid">有給</option>
            <option value="absence">欠勤</option>
            <option value="other">その他</option>
          </select>
        </label>
        <label>
          開始日
          <input
            type="date"
            required
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>
        <label>
          終了日
          <input
            type="date"
            required
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>
        <label>
          理由（任意）
          <textarea
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "送信中…" : "申請する"}
        </button>
      </form>
    </section>
  );
}
