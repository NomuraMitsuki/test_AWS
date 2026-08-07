# Phase 4 Leave API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenAPI 準拠の休暇 API（list/create/approve/reject）を leave Lambda + Terraform で実装し、pytest と terraform validate を通す（apply なし）。

**Architecture:** `backend/leave` を attendance と同型（handler/service/repository/auth/errors）。`infra/modules/api` に VPC leave Lambda と JWT ルートを追加。

**Tech Stack:** Python 3.12, pytest, Terraform, API Gateway HTTP API JWT

## Global Constraints

- apply しない。W-109 に触れない。`docs/wbs.md` は触らない
- スペック: [docs/superpowers/specs/2026-08-07-phase4-leave-api-design.md](../specs/2026-08-07-phase4-leave-api-design.md)
- OpenAPI / ER を正とする
- attendance の auth/エラーパターンを踏襲（共有化しすぎない。コピーまたは薄い共通で可）
- PR 操作しない。完了後 push

---

### Task 1: migration + leave domain + pytest

**Files:**
- Create: `backend/migrations/002_leave_requests.sql`
- Create: `backend/leave/{handler,service,repository,auth,errors}.py`
- Create: `backend/tests/test_leave.py`
- Reuse `backend/tests/lambda_loader.py` pattern for module isolation

**Behavior:**
- GET list with scope/status
- POST create → 201 pending; invalid dates → 400
- approve/reject: pending only → else 409; wrong role/team → 403

- [ ] pytest green for leave (+ existing tests still pass)
- [ ] Commit: `feat(backend): add leave API handlers and tests (W-220)`

---

### Task 2: Terraform leave Lambda + JWT routes

**Files:**
- Modify: `infra/modules/api/*` — leave Lambda (VPC), IAM, integrations, JWT routes
- Modify: `infra/envs/dev/main.tf` / outputs — wire `leave_source_dir`

**Routes:** GET/POST `/leave-requests`, POST `.../approve`, POST `.../reject`

- [ ] terraform fmt + validate
- [ ] Commit: `feat(infra): wire leave Lambda and JWT routes (W-220)`

---

### Task 3: docs（最小）

- `infra/README.md`, `docs/infra/terraform-design.md`, `docs/handoff.md`（次は W-230）
- README 索引に Phase 4 リンク
- parent design §8 に Phase 4 リンク
- **Do not** edit `docs/wbs.md`

- [ ] Commit + push `cursor/w220-leave-api-a099`

---

## 親が行うこと

- 設計レビュー → PR、WBS W-220 更新
