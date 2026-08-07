"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { RequireRole } from "@/components/RequireRole";
import { apiFetch, errorMessage } from "@/lib/api/client";
import type {
  ListResponse,
  User,
  UserRole,
  UserStatus,
} from "@/lib/api/types";

function UsersAdminInner() {
  const [items, setItems] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<UserRole>("employee");
  const [managerId, setManagerId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<ListResponse<User>>("/users");
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

  async function onInvite(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch<User>("/users", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          name: name.trim(),
          role,
          manager_id: managerId.trim() || null,
        }),
      });
      setEmail("");
      setName("");
      setManagerId("");
      setRole("employee");
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function patchUser(
    id: string,
    patch: { role?: UserRole; manager_id?: string | null; status?: UserStatus },
  ) {
    setError(null);
    try {
      await apiFetch<User>(`/users/${id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <section className="stack">
      <h1>ユーザー管理</h1>

      <h2>招待</h2>
      <form className="form" onSubmit={onInvite}>
        <label>
          メール
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          氏名
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label>
          ロール
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
          >
            <option value="employee">employee</option>
            <option value="manager">manager</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <label>
          上長 ID（任意）
          <input
            type="text"
            value={managerId}
            onChange={(e) => setManagerId(e.target.value)}
          />
        </label>
        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "招待中…" : "招待する"}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}
      <h2>一覧</h2>
      {loading ? <p>読み込み中…</p> : null}
      {!loading ? (
        <table className="table">
          <thead>
            <tr>
              <th>氏名</th>
              <th>メール</th>
              <th>ロール</th>
              <th>上長</th>
              <th>状態</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6}>ユーザーがいません</td>
              </tr>
            ) : (
              items.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>
                    <select
                      value={user.role}
                      onChange={(e) =>
                        void patchUser(user.id, {
                          role: e.target.value as UserRole,
                        })
                      }
                    >
                      <option value="employee">employee</option>
                      <option value="manager">manager</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="text"
                      defaultValue={user.manager_id ?? ""}
                      placeholder="manager_id"
                      onBlur={(e) => {
                        const next = e.target.value.trim() || null;
                        if (next !== (user.manager_id ?? null)) {
                          void patchUser(user.id, { manager_id: next });
                        }
                      }}
                    />
                  </td>
                  <td>{user.status}</td>
                  <td>
                    {user.status === "active" ? (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() =>
                          void patchUser(user.id, { status: "disabled" })
                        }
                      >
                        無効化
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="btn"
                        onClick={() =>
                          void patchUser(user.id, { status: "active" })
                        }
                      >
                        有効化
                      </button>
                    )}
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

export default function UsersAdminPage() {
  return (
    <RequireRole roles={["admin"]}>
      <UsersAdminInner />
    </RequireRole>
  );
}
