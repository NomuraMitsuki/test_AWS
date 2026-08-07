-- W-210: users + attendance_records（ER 準拠）
-- タイムスタンプは UTC 保存。work_date は JST の勤務日。

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub  VARCHAR(64)  NOT NULL UNIQUE,
    email        VARCHAR(255) NOT NULL UNIQUE,
    name         VARCHAR(120) NOT NULL,
    role         VARCHAR(20)  NOT NULL CHECK (role IN ('employee', 'manager', 'admin')),
    manager_id   UUID REFERENCES users (id),
    status       VARCHAR(20)  NOT NULL CHECK (status IN ('active', 'disabled')),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users (manager_id);

CREATE TABLE IF NOT EXISTS attendance_records (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users (id),
    work_date     DATE        NOT NULL,
    clock_in_at   TIMESTAMPTZ NOT NULL,
    clock_out_at  TIMESTAMPTZ,
    note          VARCHAR(500),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, work_date)
);

CREATE INDEX IF NOT EXISTS idx_attendance_records_user_work_date
    ON attendance_records (user_id, work_date);
