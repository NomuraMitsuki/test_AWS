"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getRoles, logout, type Role } from "@/lib/auth/session";

type NavItem = {
  href: string;
  label: string;
  roles?: Role[];
};

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "ダッシュボード" },
  { href: "/attendance", label: "打刻" },
  { href: "/attendance/history", label: "打刻履歴" },
  { href: "/attendance/summary", label: "月次サマリ" },
  { href: "/attendance/team", label: "配下勤怠", roles: ["manager", "admin"] },
  { href: "/leave", label: "休暇申請" },
  {
    href: "/leave/approvals",
    label: "休暇承認",
    roles: ["manager", "admin"],
  },
  { href: "/admin/users", label: "ユーザー管理", roles: ["admin"] },
  { href: "/exports", label: "エクスポート" },
];

function canSee(item: NavItem, roles: Role[]): boolean {
  if (!item.roles || item.roles.length === 0) return true;
  return item.roles.some((r) => roles.includes(r));
}

export function AppHeader() {
  const router = useRouter();
  const [roles, setRoles] = useState<Role[]>([]);

  useEffect(() => {
    void getRoles().then(setRoles);
  }, []);

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <header className="app-header">
      <div className="app-header-brand">勤怠管理</div>
      <nav className="app-header-nav" aria-label="メイン">
        {NAV_ITEMS.filter((item) => canSee(item, roles)).map((item) => (
          <Link key={item.href} href={item.href}>
            {item.label}
          </Link>
        ))}
      </nav>
      <button type="button" className="btn-secondary" onClick={handleLogout}>
        ログアウト
      </button>
    </header>
  );
}
