"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "aws-amplify/auth";
import { configureAmplify } from "@/lib/auth/amplify";
import { isAuthenticated } from "@/lib/auth/session";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    configureAmplify();
    void isAuthenticated().then((ok) => {
      if (ok) router.replace("/");
    });
  }, [router]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    configureAmplify();

    try {
      const result = await signIn({ username: email.trim(), password });
      const step = result.nextStep.signInStep;

      if (step === "CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED") {
        sessionStorage.setItem("pendingNewPasswordEmail", email.trim());
        router.push("/login/new-password");
        return;
      }

      if (step === "DONE" || result.isSignedIn) {
        router.replace("/");
        return;
      }

      setError(`追加の認証手順が必要です: ${step}`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "ログインに失敗しました";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-panel">
        <h1>勤怠管理</h1>
        <p className="lead">メールアドレスとパスワードでログイン</p>
        <form className="form" onSubmit={onSubmit}>
          <label>
            メールアドレス
            <input
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            パスワード
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "ログイン中…" : "ログイン"}
          </button>
        </form>
      </div>
    </div>
  );
}
