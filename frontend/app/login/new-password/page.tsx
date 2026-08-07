"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { confirmSignIn } from "aws-amplify/auth";
import { configureAmplify } from "@/lib/auth/amplify";

export default function NewPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    configureAmplify();
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirm) {
      setError("パスワードが一致しません");
      return;
    }

    setSubmitting(true);
    configureAmplify();

    try {
      const result = await confirmSignIn({ challengeResponse: password });
      if (result.isSignedIn || result.nextStep.signInStep === "DONE") {
        sessionStorage.removeItem("pendingNewPasswordEmail");
        router.replace("/");
        return;
      }
      setError(`追加の認証手順が必要です: ${result.nextStep.signInStep}`);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "パスワード変更に失敗しました。ログインからやり直してください。";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-panel">
        <h1>仮パスワード変更</h1>
        <p className="lead">初回ログイン用の新しいパスワードを設定してください</p>
        <form className="form" onSubmit={onSubmit}>
          <label>
            新しいパスワード
            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <label>
            新しいパスワード（確認）
            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "変更中…" : "パスワードを設定"}
          </button>
        </form>
      </div>
    </div>
  );
}
