"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { configureAmplify } from "@/lib/auth/amplify";
import { isAuthenticated } from "@/lib/auth/session";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_DEMO_MODE !== "true") {
      configureAmplify();
    }
    void isAuthenticated().then((ok) => {
      if (!ok) {
        router.replace("/login");
        return;
      }
      setReady(true);
    });
  }, [router]);

  if (!ready) {
    return (
      <main>
        <p>認証を確認しています…</p>
      </main>
    );
  }

  return (
    <>
      <AppHeader />
      <main>{children}</main>
    </>
  );
}
