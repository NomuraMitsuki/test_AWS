"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type { ExportResult, Scope } from "@/lib/api/types";
import { getRoles } from "@/lib/auth/session";

export default function ExportsPage() {
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [scope, setScope] = useState<Scope>("self");
  const [allowedScopes, setAllowedScopes] = useState<Scope[]>(["self"]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    void getRoles().then((roles) => {
      if (roles.includes("admin")) {
        setAllowedScopes(["self", "team", "all"]);
      } else if (roles.includes("manager")) {
        setAllowedScopes(["self", "team"]);
      } else {
        setAllowedScopes(["self"]);
      }
    });
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const result = await apiFetch<ExportResult>("/exports/attendance", {
        method: "POST",
        body: JSON.stringify({
          from_date: fromDate,
          to_date: toDate,
          scope,
        }),
      });
      window.open(result.download_url, "_blank", "noopener,noreferrer");
      setMessage("ダウンロードを開始しました。");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="stack">
      <h1>勤怠エクスポート</h1>
      <p>期間を指定して CSV をダウンロードします。</p>
      <form className="form" onSubmit={onSubmit}>
        <label>
          開始日
          <input
            type="date"
            required
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
          />
        </label>
        <label>
          終了日
          <input
            type="date"
            required
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
          />
        </label>
        <label>
          範囲
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value as Scope)}
          >
            {allowedScopes.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="ok">{message}</p> : null}
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "生成中…" : "CSV をダウンロード"}
        </button>
      </form>
    </section>
  );
}
