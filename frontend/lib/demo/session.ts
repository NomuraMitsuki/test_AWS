import type { Role } from "@/lib/auth/session";

const STORAGE_KEY = "attendance_demo_session";

export type DemoSession = {
  role: Role;
  userId: string;
  email: string;
  name: string;
};

const DEMO_USERS: Record<Role, DemoSession> = {
  employee: {
    role: "employee",
    userId: "user-employee-1",
    email: "employee@example.com",
    name: "一般 太郎",
  },
  manager: {
    role: "manager",
    userId: "user-manager-1",
    email: "manager@example.com",
    name: "上長 花子",
  },
  admin: {
    role: "admin",
    userId: "user-admin-1",
    email: "admin@example.com",
    name: "管理者 次郎",
  },
};

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof sessionStorage !== "undefined";
}

export function getDemoSession(): DemoSession | null {
  if (!canUseStorage()) return null;
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as DemoSession;
  } catch {
    return null;
  }
}

export function startDemoSession(role: Role): DemoSession {
  const session = DEMO_USERS[role];
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  return session;
}

export function clearDemoSession(): void {
  if (!canUseStorage()) return;
  sessionStorage.removeItem(STORAGE_KEY);
}

export function demoRoles(): Role[] {
  return ["employee", "manager", "admin"];
}
