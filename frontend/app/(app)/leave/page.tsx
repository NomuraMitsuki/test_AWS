"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { LeaveRequest, ListResponse } from "@/lib/api/types";
import { getRoles } from "@/lib/auth/session";

const LEAVE_TYPE_LABEL: Record<string, string> = {
  paid: "有給",
  absence: "欠勤",
  other: "その他",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "承認待ち",
  approved: "承認済",
  rejected: "却下",
};

export default function LeaveListPage() {
  const [items, setItems] = useState<LeaveRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [canApprove, setCanApprove] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const roles = await getRoles();
        setCanApprove(roles.includes("manager") || roles.includes("admin"));
        const data = await apiFetch<ListResponse<LeaveRequest>>(
          "/leave-requests?scope=self",
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
      <h1>休暇申請一覧</h1>
      <div className="row">
        <Link href="/leave/new">新規申請</Link>
        {canApprove ? <Link href="/leave/approvals">承認画面へ</Link> : null}
      </div>
      {loading ? <p>読み込み中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error ? (
        <table className="table">
          <thead>
            <tr>
              <th>種別</th>
              <th>開始</th>
              <th>終了</th>
              <th>状態</th>
              <th>理由</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5}>申請がありません</td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id}>
                  <td>{LEAVE_TYPE_LABEL[row.leave_type] ?? row.leave_type}</td>
                  <td>{row.start_date}</td>
                  <td>{row.end_date}</td>
                  <td>{STATUS_LABEL[row.status] ?? row.status}</td>
                  <td>{row.comment ?? "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
