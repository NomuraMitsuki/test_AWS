import type {
  ApiError,
  AttendanceRecord,
  AttendanceSummary,
  ExportResult,
  LeaveRequest,
  LeaveRequestCreate,
  ListResponse,
  User,
  UserInvite,
  UserUpdate,
} from "@/lib/api/types";
import { todayLocalDate } from "@/lib/dates";
import {
  DEMO_USERS,
  initialAttendance,
  initialLeave,
} from "./fixtures";
import { getDemoSession } from "./session";

type Store = {
  attendance: AttendanceRecord[];
  leave: LeaveRequest[];
  users: User[];
  seq: number;
};

const STORE_KEY = "attendance_demo_store";

function loadStore(): Store {
  if (typeof window === "undefined") {
    return {
      attendance: initialAttendance(),
      leave: initialLeave(),
      users: [...DEMO_USERS],
      seq: 100,
    };
  }
  const raw = sessionStorage.getItem(STORE_KEY);
  if (raw) {
    try {
      return JSON.parse(raw) as Store;
    } catch {
      /* fall through */
    }
  }
  const store: Store = {
    attendance: initialAttendance(),
    leave: initialLeave(),
    users: [...DEMO_USERS],
    seq: 100,
  };
  sessionStorage.setItem(STORE_KEY, JSON.stringify(store));
  return store;
}

function saveStore(store: Store): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STORE_KEY, JSON.stringify(store));
}

function nextId(store: Store, prefix: string): string {
  store.seq += 1;
  return `${prefix}-${store.seq}`;
}

function fail(status: number, message: string): never {
  throw { status, message } satisfies ApiError;
}

function parseQuery(path: string): { pathname: string; params: URLSearchParams } {
  const [pathname, qs] = path.split("?");
  return { pathname, params: new URLSearchParams(qs ?? "") };
}

function teamUserIds(store: Store, managerId: string): string[] {
  return store.users
    .filter((u) => u.manager_id === managerId || u.id === managerId)
    .map((u) => u.id);
}

function filterAttendance(
  store: Store,
  scope: string,
  from: string | null,
  to: string | null,
  sessionUserId: string,
): AttendanceRecord[] {
  let items = [...store.attendance];
  if (scope === "self") {
    items = items.filter((r) => r.user_id === sessionUserId);
  } else if (scope === "team") {
    const ids = new Set(teamUserIds(store, sessionUserId));
    items = items.filter((r) => ids.has(r.user_id));
  }
  if (from) items = items.filter((r) => r.work_date >= from);
  if (to) items = items.filter((r) => r.work_date <= to);
  items.sort((a, b) => b.work_date.localeCompare(a.work_date));
  return items;
}

function filterLeave(
  store: Store,
  scope: string,
  status: string | null,
  sessionUserId: string,
): LeaveRequest[] {
  let items = [...store.leave];
  if (scope === "self") {
    items = items.filter((r) => r.user_id === sessionUserId);
  } else if (scope === "team") {
    const ids = new Set(
      store.users
        .filter((u) => u.manager_id === sessionUserId)
        .map((u) => u.id),
    );
    items = items.filter((r) => ids.has(r.user_id));
  }
  if (status) items = items.filter((r) => r.status === status);
  return items;
}

function summaryFor(
  store: Store,
  userId: string,
  year: number,
  month: number,
): AttendanceSummary {
  const prefix = `${year}-${String(month).padStart(2, "0")}`;
  const records = store.attendance.filter(
    (r) => r.user_id === userId && r.work_date.startsWith(prefix),
  );
  let total = 0;
  for (const r of records) {
    if (!r.clock_out_at) continue;
    const start = new Date(r.clock_in_at).getTime();
    const end = new Date(r.clock_out_at).getTime();
    if (!Number.isNaN(start) && !Number.isNaN(end) && end > start) {
      total += Math.round((end - start) / 60000);
    }
  }
  return {
    year,
    month,
    total_work_minutes: total,
    work_days: records.filter((r) => r.clock_out_at).length,
    records,
  };
}

export async function mockApiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const session = getDemoSession();
  if (!session) {
    fail(401, "ログインが必要です");
  }

  const method = (init.method ?? "GET").toUpperCase();
  const { pathname, params } = parseQuery(path);
  const store = loadStore();
  let body: unknown = null;
  if (init.body && typeof init.body === "string") {
    try {
      body = JSON.parse(init.body);
    } catch {
      body = null;
    }
  }

  // Attendance
  if (pathname === "/attendance/records" && method === "GET") {
    const scope = params.get("scope") ?? "self";
    const items = filterAttendance(
      store,
      scope,
      params.get("from"),
      params.get("to"),
      session.userId,
    );
    return { items } as T;
  }

  if (pathname === "/attendance/clock-in" && method === "POST") {
    const today = todayLocalDate();
    const existing = store.attendance.find(
      (r) => r.user_id === session.userId && r.work_date === today,
    );
    if (existing && !existing.clock_out_at) {
      fail(409, "すでに出勤中です");
    }
    if (existing?.clock_out_at) {
      fail(409, "本日はすでに退勤済みです");
    }
    const created: AttendanceRecord = {
      id: nextId(store, "att"),
      user_id: session.userId,
      work_date: today,
      clock_in_at: new Date().toISOString(),
      clock_out_at: null,
      note: null,
    };
    store.attendance.unshift(created);
    saveStore(store);
    return created as T;
  }

  if (pathname === "/attendance/clock-out" && method === "POST") {
    const today = todayLocalDate();
    const open = store.attendance.find(
      (r) =>
        r.user_id === session.userId &&
        r.work_date === today &&
        !r.clock_out_at,
    );
    if (!open) {
      fail(409, "出勤中のレコードがありません");
    }
    open.clock_out_at = new Date().toISOString();
    saveStore(store);
    return open as T;
  }

  if (pathname === "/attendance/summary" && method === "GET") {
    const now = new Date();
    const year = Number(params.get("year") ?? now.getFullYear());
    const month = Number(params.get("month") ?? now.getMonth() + 1);
    const userId = params.get("user_id") ?? session.userId;
    return summaryFor(store, userId, year, month) as T;
  }

  // Leave
  if (pathname === "/leave-requests" && method === "GET") {
    const scope = params.get("scope") ?? "self";
    const items = filterLeave(
      store,
      scope,
      params.get("status"),
      session.userId,
    );
    return { items } satisfies ListResponse<LeaveRequest> as T;
  }

  if (pathname === "/leave-requests" && method === "POST") {
    const input = body as LeaveRequestCreate;
    const created: LeaveRequest = {
      id: nextId(store, "leave"),
      user_id: session.userId,
      leave_type: input.leave_type,
      start_date: input.start_date,
      end_date: input.end_date,
      comment: input.comment,
      status: "pending",
      approver_id: null,
      reject_reason: null,
      created_at: new Date().toISOString(),
    };
    store.leave.unshift(created);
    saveStore(store);
    return created as T;
  }

  const approveMatch = pathname.match(
    /^\/leave-requests\/([^/]+)\/approve$/,
  );
  if (approveMatch && method === "POST") {
    const item = store.leave.find((r) => r.id === approveMatch[1]);
    if (!item) fail(404, "休暇申請が見つかりません");
    item.status = "approved";
    item.approver_id = session.userId;
    item.reject_reason = null;
    saveStore(store);
    return item as T;
  }

  const rejectMatch = pathname.match(/^\/leave-requests\/([^/]+)\/reject$/);
  if (rejectMatch && method === "POST") {
    const item = store.leave.find((r) => r.id === rejectMatch[1]);
    if (!item) fail(404, "休暇申請が見つかりません");
    const reason =
      body && typeof body === "object" && "reason" in body
        ? String((body as { reason?: string }).reason ?? "却下")
        : "却下";
    item.status = "rejected";
    item.approver_id = session.userId;
    item.reject_reason = reason;
    saveStore(store);
    return item as T;
  }

  // Users
  if (pathname === "/users" && method === "GET") {
    return { items: store.users } satisfies ListResponse<User> as T;
  }

  if (pathname === "/users" && method === "POST") {
    const input = body as UserInvite;
    const created: User = {
      id: nextId(store, "user"),
      email: input.email,
      name: input.name,
      role: input.role,
      manager_id: input.manager_id ?? null,
      status: "active",
    };
    store.users.push(created);
    saveStore(store);
    return created as T;
  }

  const userMatch = pathname.match(/^\/users\/([^/]+)$/);
  if (userMatch && method === "PATCH") {
    const user = store.users.find((u) => u.id === userMatch[1]);
    if (!user) fail(404, "ユーザーが見つかりません");
    const input = body as UserUpdate;
    if (input.role !== undefined) user.role = input.role;
    if (input.manager_id !== undefined) user.manager_id = input.manager_id;
    if (input.status !== undefined) user.status = input.status;
    saveStore(store);
    return user as T;
  }

  // Exports
  if (pathname === "/exports/attendance" && method === "POST") {
    const csv =
      "user_id,work_date,clock_in_at,clock_out_at\n" +
      store.attendance
        .map(
          (r) =>
            `${r.user_id},${r.work_date},${r.clock_in_at},${r.clock_out_at ?? ""}`,
        )
        .join("\n");
    const download_url = `data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`;
    const result: ExportResult = {
      export_job_id: nextId(store, "export"),
      download_url,
      expires_in: 300,
    };
    saveStore(store);
    return result as T;
  }

  fail(404, `デモ Mock 未対応: ${method} ${pathname}`);
}
