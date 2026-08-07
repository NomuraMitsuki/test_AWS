# Phase 2 HTTP API + health Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** `GET /health` 用 Python Lambda と、Cognito JWT authorizer 付き HTTP API を Terraform で再現可能にし、apply なしで pytest / terraform validate まで通す（W-200）。

**Architecture:** `backend/health` に薄いハンドラ。`infra/modules/api` が Lambda・HTTP API・JWT authorizer・`GET /health`（authorizer なし）を定義し、`infra/envs/dev` から Cognito 出力を渡す。

**Tech Stack:** Python 3.12, pytest, Terraform AWS provider ~> 5.x, API Gateway HTTP API (apigatewayv2)

## Global Constraints

- apply / AWS デプロイはしない
- リージョン `ap-northeast-1`、name_prefix `attendance-dev-*`
- health Lambda は VPC 外
- 日本語ドキュメント・コミットメッセージ可。識別子は英語
- スペック: [docs/superpowers/specs/2026-08-07-phase2-http-api-health-design.md](../specs/2026-08-07-phase2-http-api-health-design.md)
- OpenAPI: [docs/api/openapi.yaml](../../api/openapi.yaml) の `/health`

---

### Task 1: health Lambda + pytest

**Files:**
- Create: `backend/health/handler.py`
- Create: `backend/health/requirements.txt`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/conftest.py`（不要なら省略可）
- Create: `backend/requirements-dev.txt`（pytest）

**Interfaces:**
- Produces: `handler(event, context) -> dict` with `statusCode` 200 and JSON body `{"status":"ok"}` for API Gateway HTTP API payload 2.0

- [x] **Step 1: Write failing test** in `backend/tests/test_health.py` that imports `handler.handler` and asserts 200 + `status=ok`
- [x] **Step 2: Run** `cd backend && pip install -q pytest && PYTHONPATH=health pytest tests/test_health.py -v` → expect FAIL
- [x] **Step 3: Implement** minimal `handler.py`
- [x] **Step 4: Re-run pytest** → PASS
- [x] **Step 5: Commit** `feat(backend): add health Lambda handler and pytest (W-200)`

---

### Task 2: Terraform `modules/api`

**Files:**
- Create: `infra/modules/api/main.tf`
- Create: `infra/modules/api/variables.tf`
- Create: `infra/modules/api/outputs.tf`
- Create: `infra/modules/api/versions.tf`（必要なら。archive / aws プロバイダ）

**Interfaces:**
- Consumes: `name_prefix`, `cognito_user_pool_id`, `cognito_client_id`, `cognito_issuer_url`, path to health source
- Produces: `api_endpoint`, `health_lambda_function_name`, `http_api_id`
- Resources: IAM role, Lambda (python3.12, archive_file from backend/health), HTTP API, stage `$default`, JWT authorizer (Cognito), route `GET /health` without authorizer, lambda permission

- [x] **Step 1: Implement module files**
- [x] **Step 2: Commit** `feat(infra): add api module with HTTP API JWT and health route`

---

### Task 3: Wire `envs/dev` + docs

**Files:**
- Modify: `infra/envs/dev/main.tf` — add `module.api`
- Modify: `infra/envs/dev/outputs.tf` — expose api outputs
- Modify: `infra/README.md` — api モジュール一行
- Modify: `docs/wbs.md` — W-200 を進行中（完了は PR 後に親が確定してもよいが、実装完了なら完了＋本ブランチとメモ）
- Modify: `docs/handoff.md` — 次作業を更新
- Modify: `docs/infra/terraform-design.md` — api モジュールが実装済みである旨（必要最小限）
- Modify: root `README.md` — backend に言及があれば更新

- [x] **Step 1: Wire module.api** using cognito outputs; set `health_source_dir` to absolute or relative path that works from `envs/dev` (e.g. `${path.root}/../../../backend/health`)
- [x] **Step 2: Run** `cd infra/envs/dev && terraform init -backend=false && terraform validate` and `terraform fmt -check -recursive ../..`
- [x] **Step 3: Update docs**
- [x] **Step 4: Commit** `feat(infra): wire api module in dev and update W-200 docs`
- [x] **Step 5: Push** branch `cursor/w200-http-api-health-a099`（force-with-lease if rebased）

---

## 親が行うこと（ワーカーはしない）

- 設計資料レビュー（`review-design-docs`）
- PR 作成
- WBS 最終ステータスの確定（ワーカーが更新した場合は親が確認）
