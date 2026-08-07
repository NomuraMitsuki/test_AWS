export type ApiError = {
  status: number;
  message: string;
  code?: string;
  request_id?: string;
};

export type Scope = "self" | "team" | "all";

export type AttendanceRecord = {
  id: string;
  user_id: string;
  work_date: string;
  clock_in_at: string;
  clock_out_at: string | null;
  note: string | null;
};

export type AttendanceSummary = {
  year: number;
  month: number;
  total_work_minutes: number;
  work_days: number;
  records: AttendanceRecord[];
};

export type LeaveType = "paid" | "absence" | "other";
export type LeaveStatus = "pending" | "approved" | "rejected";

export type LeaveRequest = {
  id: string;
  user_id: string;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  comment?: string;
  status: LeaveStatus;
  approver_id: string | null;
  reject_reason: string | null;
  created_at: string;
};

export type LeaveRequestCreate = {
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  comment?: string;
};

export type UserRole = "employee" | "manager" | "admin";
export type UserStatus = "active" | "disabled";

export type User = {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  manager_id: string | null;
  status: UserStatus;
};

export type UserInvite = {
  email: string;
  name: string;
  role: UserRole;
  manager_id?: string | null;
};

export type UserUpdate = {
  role?: UserRole;
  manager_id?: string | null;
  status?: UserStatus;
};

export type ExportRequest = {
  from_date: string;
  to_date: string;
  scope: Scope;
};

export type ExportResult = {
  export_job_id: string;
  download_url: string;
  expires_in: number;
};

export type ListResponse<T> = {
  items: T[];
};
