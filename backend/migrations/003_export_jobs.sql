-- W-240: export_jobs（ER 準拠）
-- users / attendance_records は 001_init_attendance.sql 前提。

CREATE TABLE IF NOT EXISTS export_jobs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requested_by   UUID        NOT NULL REFERENCES users (id),
    s3_key         VARCHAR(512),
    status         VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed')),
    scope          VARCHAR(20) NOT NULL CHECK (scope IN ('self', 'team', 'all')),
    from_date      DATE        NOT NULL,
    to_date        DATE        NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at   TIMESTAMPTZ,
    CHECK (from_date <= to_date)
);

CREATE INDEX IF NOT EXISTS idx_export_jobs_requested_by_status
    ON export_jobs (requested_by, status);
