import type {
  AttendanceRecord,
  LeaveRequest,
  User,
} from "@/lib/api/types";
import { todayLocalDate } from "@/lib/dates";

const today = todayLocalDate();

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export const DEMO_USERS: User[] = [
  {
    id: "user-admin-1",
    email: "admin@example.com",
    name: "管理者 次郎",
    role: "admin",
    manager_id: null,
    status: "active",
  },
  {
    id: "user-manager-1",
    email: "manager@example.com",
    name: "上長 花子",
    role: "manager",
    manager_id: "user-admin-1",
    status: "active",
  },
  {
    id: "user-employee-1",
    email: "employee@example.com",
    name: "一般 太郎",
    role: "employee",
    manager_id: "user-manager-1",
    status: "active",
  },
  {
    id: "user-employee-2",
    email: "employee2@example.com",
    name: "一般 三郎",
    role: "employee",
    manager_id: "user-manager-1",
    status: "active",
  },
];

export function initialAttendance(): AttendanceRecord[] {
  return [
    {
      id: "att-1",
      user_id: "user-employee-1",
      work_date: daysAgo(1),
      clock_in_at: `${daysAgo(1)}T09:00:00+09:00`,
      clock_out_at: `${daysAgo(1)}T18:00:00+09:00`,
      note: null,
    },
    {
      id: "att-2",
      user_id: "user-employee-1",
      work_date: daysAgo(2),
      clock_in_at: `${daysAgo(2)}T09:05:00+09:00`,
      clock_out_at: `${daysAgo(2)}T18:10:00+09:00`,
      note: null,
    },
    {
      id: "att-3",
      user_id: "user-employee-2",
      work_date: today,
      clock_in_at: `${today}T09:00:00+09:00`,
      clock_out_at: null,
      note: null,
    },
    {
      id: "att-4",
      user_id: "user-manager-1",
      work_date: today,
      clock_in_at: `${today}T08:45:00+09:00`,
      clock_out_at: null,
      note: null,
    },
  ];
}

export function initialLeave(): LeaveRequest[] {
  return [
    {
      id: "leave-1",
      user_id: "user-employee-1",
      leave_type: "paid",
      start_date: daysAgo(-3),
      end_date: daysAgo(-3),
      comment: "私用",
      status: "pending",
      approver_id: null,
      reject_reason: null,
      created_at: `${daysAgo(1)}T10:00:00+09:00`,
    },
    {
      id: "leave-2",
      user_id: "user-employee-2",
      leave_type: "absence",
      start_date: daysAgo(-5),
      end_date: daysAgo(-5),
      comment: "体調不良",
      status: "pending",
      approver_id: null,
      reject_reason: null,
      created_at: `${daysAgo(2)}T11:00:00+09:00`,
    },
    {
      id: "leave-3",
      user_id: "user-employee-1",
      leave_type: "paid",
      start_date: daysAgo(10),
      end_date: daysAgo(10),
      status: "approved",
      approver_id: "user-manager-1",
      reject_reason: null,
      created_at: `${daysAgo(12)}T09:00:00+09:00`,
    },
  ];
}
