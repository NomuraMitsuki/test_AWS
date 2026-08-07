# Phase 5 Users API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenAPI 準拠のユーザー一覧・招待・更新 API を users Lambda + Terraform で実装し、pytest と terraform validate を通す（apply なし）。

**Architecture:** `backend/users` を leave/attendance と同型。Cognito 操作は `cognito_client` 境界でモック可能。`infra/modules/api` に VPC users Lambda + JWT ルート。

**Tech Stack:** Python 3.12, pytest, Terraform, API Gateway HTTP API JWT

## Global Constraints

- apply しない。W-109 に触れない。`docs/wbs.md` は触らない
- スペック: [docs/superpowers/specs/2026-08-07-phase5-users-api-design.md](../specs/2026-08-07-phase5-users-api-design.md)
- OpenAPI / 親スペック §4.4.1 を正とする
- PR 操作しない。完了後 push

---

### Task 1: users domain + pytest

**Files:**
- Create: `backend/users/{handler,service,repository,auth,errors,cognito}.py`
- Create: `backend/tests/test_users.py`
- Update: `backend/tests/lambda_loader.py` for users
- Optionally: `backend/migrations/003_*.sql` if needed (users already in 001)

**Behavior:**
- GET/POST /users, PATCH /users/{id} — admin only
- invite duplicate email → 409; missing id → 404; non-admin → 403

- [x] pytest green (all suites)
- [x] Commit: `feat(backend): add users API handlers and tests (W-230)`

---

### Task 2: Terraform users Lambda + JWT routes

- Modify `infra/modules/api/*` and `infra/envs/dev/*`
- IAM: VPC + secrets + Cognito admin actions (UserPool scoped) for invite/group sync

- [x] terraform fmt + validate
- [x] Commit: `feat(infra): wire users Lambda and JWT routes (W-230)`

---

### Task 3: docs（最小）

- infra README, terraform-design, handoff（次は W-240）, README 索引, parent §8 Phase 5 link
- Do not edit docs/wbs.md

- [x] Commit + push `cursor/w230-users-api-a099`

---

## 親が行うこと

- 設計レビュー → PR、WBS 更新
