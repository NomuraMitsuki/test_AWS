# Phase 3 Attendance API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenAPI 準拠の勤怠 API（clock-in/out, records, me, summary）を attendance Lambda + Terraform ルートで実装し、pytest と terraform validate を通す（apply なし）。

**Architecture:** `backend/attendance` にルーティングとユースケース。DB アクセスはリポジトリ境界面でモック可能にする。`infra/modules/api` に VPC 付き attendance Lambda と JWT 必須ルートを追加。

**Tech Stack:** Python 3.12, pytest, Terraform aws/archive, API Gateway HTTP API JWT authorizer（既存）

## Global Constraints

- apply しない。W-109 に触れない
- スペック: [docs/superpowers/specs/2026-08-07-phase3-attendance-api-design.md](../specs/2026-08-07-phase3-attendance-api-design.md)
- OpenAPI / ER を正とする
- health Lambda の VPC 外方針は維持
- `docs/wbs.md` のステータス更新は親が行う（ワーカーは触らない）
- PR 操作しない。完了後 push

---

### Task 1: migrations + attendance ドメイン骨格 + pytest

**Files:**
- Create: `backend/migrations/001_init_attendance.sql`（users + attendance_records）
- Create: `backend/attendance/handler.py`（HTTP API 2.0 ルーティング）
- Create: `backend/attendance/service.py`（打刻・履歴・サマリ）
- Create: `backend/attendance/repository.py`（IF + インメモリ実装をテスト用に）
- Create: `backend/attendance/auth.py`（JWT claims / ロール判定ヘルパ。テストでは event.requestContext.authorizer.jwt.claims を想定）
- Create: `backend/attendance/errors.py`（共通 Error JSON）
- Create: `backend/tests/test_attendance.py`
- Modify: `backend/requirements-dev.txt` if needed

**Behavior:**
- clock-in: 当日未打刻なら作成 201。既存なら 409 `ALREADY_CLOCKED_IN`
- clock-out: 出勤済・未退勤なら更新 200。未出勤/済退勤は 409
- records/me/summary: OpenAPI の scope / 権限に従う（インメモリ users で manager/admin を検証）

- [ ] Implement + pytest green
- [ ] Commit: `feat(backend): add attendance API handlers and tests (W-210)`

---

### Task 2: Terraform — attendance Lambda + JWT routes

**Files:**
- Modify: `infra/modules/api/main.tf` — attendance Lambda（VPC: private subnets + lambda SG）、IAM（Basic + VPC access + secretsmanager GetSecretValue）、routes with `authorization_type = JWT` + authorizer_id
- Modify: `infra/modules/api/variables.tf` — private_subnet_ids, lambda_security_group_id, db_secret_arn, attendance_source_dir
- Modify: `infra/modules/api/outputs.tf`
- Modify: `infra/envs/dev/main.tf` — pass network/data outputs into api module

**Routes:** POST clock-in/out, GET records/me/summary — all JWT

- [ ] terraform fmt + validate
- [ ] Commit: `feat(infra): wire attendance Lambda and JWT routes (W-210)`

---

### Task 3: docs（付随・最小）

**Files:**
- Modify: `infra/README.md`, `docs/infra/terraform-design.md`, `docs/handoff.md`（次は W-220）
- Modify: parent design §8 link to Phase 3 if missing
- **Do not** modify `docs/wbs.md` W-210 status（親が更新）

- [ ] Commit + push `cursor/w210-attendance-api-a099`

---

## 親が行うこと

- 設計レビュー → PR 作成
- WBS W-210 完了更新
