# Phase 6 Exports API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenAPI 準拠の勤怠 CSV エクスポート API を exports Lambda + Terraform で実装し、pytest と terraform validate を通す（apply なし）。

**Architecture:** `backend/exports` 同型構成。S3 は `storage` クライアント境界でモック。`infra/modules/api` に VPC exports Lambda + JWT ルート + S3 IAM。`storage` モジュールの bucket 名/ARN を渡す。

**Tech Stack:** Python 3.12, pytest, Terraform, S3 presigned URL

## Global Constraints

- apply しない。W-109 に触れない。`docs/wbs.md` は触らない
- スペック: [docs/superpowers/specs/2026-08-07-phase6-exports-api-design.md](../specs/2026-08-07-phase6-exports-api-design.md)
- OpenAPI / シーケンス §4 を正とする
- PR 操作しない。完了後 push

---

### Task 1: migration + exports domain + pytest

**Files:**
- Create: `backend/migrations/003_export_jobs.sql`
- Create: `backend/exports/{handler,service,repository,auth,errors,storage}.py`
- Create: `backend/tests/test_exports.py`
- Update: `backend/tests/lambda_loader.py`

**Behavior:**
- POST /exports/attendance — scope 認可、CSV 生成、モック S3、200 with download_url
- invalid dates → 400; forbidden scope → 403

- [x] pytest green (all suites)
- [x] Commit: `feat(backend): add exports API handlers and tests (W-240)`

---

### Task 2: Terraform exports Lambda + JWT + S3 IAM

- Modify `infra/modules/api/*`, `infra/envs/dev/*` — pass exports bucket name/arn from storage module

- [x] terraform fmt + validate
- [x] Commit: `feat(infra): wire exports Lambda JWT route and S3 IAM (W-240)`

---

### Task 3: docs（最小）

- infra README, terraform-design, handoff（次は W-250）, README 索引, parent §8 Phase 6
- Do not edit docs/wbs.md

- [x] Commit + push `cursor/w240-exports-api-a099`

---

## 親が行うこと

- 設計レビュー → PR、WBS 更新
