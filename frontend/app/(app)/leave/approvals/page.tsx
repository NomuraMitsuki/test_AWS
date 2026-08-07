"use client";

import { useCallback, useEffect, useState } from "react";
import { RequireRole } from "@/components/RequireRole";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { LeaveRequest, ListResponse } from "@/lib/api/types";
import { getRoles } from "@/lib/auth/session";

const LEAVE_TYPE_LABEL: Record<string, string> = {
  paid: "有給",
  absence: "欠勤",
  other: "その他",
};

function ApprovalsInner() {
  const [items, setItems] = useState<LeaveRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const roles = await getRoles();
      const scope = roles.includes("admin") ? "all" : "team";
      const data = await apiFetch<ListResponse<LeaveRequest>>(
        `/leave-requests?scope=${scope}&status=pending`,
      );
      setItems(data.items);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function approve(id: string) {
    setBusyId(id);
    setError(null);
    try {
      await apiFetch<LeaveRequest>(`/leave-requests/${id}/approve`, {
        method: "POST",
      });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function reject(id: string) {
    const reason = window.prompt("却下理由（任意）") ?? "";
    setBusyId(id);
    setError(null);
    try {
      await apiFetch<LeaveRequest>(`/leave-requests/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({
          reject_reason: reason.trim() || undefined,
        }),
      });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="stack">
      <h1>休暇承認</h1>
      <p>承認待ちの申請を処理します。</p>
      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading ? (
        <table className="table">
          <thead>
            <tr>
              <th>申請者</th>
              <th>種別</th>
              <th>期間</th>
              <th>理由</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5}>承認待ちはありません</td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id}>
                  <td>{row.user_id}</td>
                  <td>{LEAVE_TYPE_LABEL[row.leave_type] ?? row.leave_type}</td>
                  <td>
                    {row.start_date} 〜 {row.end_date}
                  </td>
                  <td>{row.comment ?? "—"}</td>
                  <td>
                    <div className="row">
                      <button
                        type="button"
                        className="btn"
                        disabled={busyId === row.id}
                        onClick={() => void approve(row.id)}
                      >
                        承認
                      </button>
                      <button
                        type="button"
                        className="btn-secondary"
                        disabled={busyId === row.id}
                        onClick={() => void reject(row.id)}
                      >
                        却下
                      </button>
                    </div>
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

export default function LeaveApprovalsPage() {
  return (
    <RequireRole roles={["manager", "admin"]}>
      <ApprovalsInner />
    </RequireRole>
  );
}
