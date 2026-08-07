"use client";

import { useEffect, useState, type ReactNode } from "react";
import { getRoles, type Role } from "@/lib/auth/session";

type Props = {
  roles: Role[];
  children: ReactNode;
};

export function RequireRole({ roles, children }: Props) {
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    void getRoles().then((userRoles) => {
      setAllowed(roles.some((r) => userRoles.includes(r)));
    });
  }, [roles]);

  if (allowed === null) {
    return <p>確認中…</p>;
  }

  if (!allowed) {
    return (
      <section>
        <h1>アクセス権限がありません</h1>
        <p>この画面を表示する権限がありません（403）。</p>
      </section>
    );
  }

  return <>{children}</>;
}
