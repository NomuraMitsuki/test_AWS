-- W-220: leave_requests（ER 準拠）
-- users / attendance_records は 001_init_attendance.sql 前提。

CREATE TABLE IF NOT EXISTS leave_requests (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users (id),
    leave_type    VARCHAR(20) NOT NULL CHECK (leave_type IN ('paid', 'absence', 'other')),
    start_date    DATE        NOT NULL,
    end_date      DATE        NOT NULL,
    status        VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    approver_id   UUID REFERENCES users (id),
    comment       TEXT,
    reject_reason TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (start_date <= end_date)
);

CREATE INDEX IF NOT EXISTS idx_leave_requests_user_status
    ON leave_requests (user_id, status);
