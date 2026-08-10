# Phase 9 Monitoring Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本リポジトリでは親が `implementation-worker` に本計画全体を委譲してもよい。

**Goal:** CloudWatch ダッシュボードと主要アラームを `monitoring` モジュールに実装し、`envs/dev` から API / Lambda / RDS を配線して terraform validate を通す（apply なし）。

**Architecture:** 既存 SNS を維持。dashboard_body をメトリクス／ログウィジェットに拡張。アラームは Lambda×5・API 5xx・Latency p99・RDS CPU/Connections。`module.api` / `module.data` の出力を monitoring に渡す。

**Tech Stack:** Terraform 1.9.x, AWS CloudWatch, SNS

## Global Constraints

- apply しない。W-109 に触れない
- スペック: [docs/superpowers/specs/2026-08-10-phase9-monitoring-polish-design.md](../specs/2026-08-10-phase9-monitoring-polish-design.md)
- 正本: [docs/ops/monitoring.md](../../ops/monitoring.md)
- `docs/wbs.md` ステータスは触らない（親が更新）
- PR 操作しない。ブランチ `cursor/w270-monitoring-a099` で push
- Lambda ロググループの retention 管理は非ゴール（ダッシュボードは名前参照のみ）

## File structure

```text
infra/modules/monitoring/main.tf       # dashboard + alarms
infra/modules/monitoring/variables.tf  # http_api_id, lambdas, db_instance_id
infra/modules/monitoring/outputs.tf    # 必要なら alarm ARNs
infra/envs/dev/main.tf                 # wiring
docs/ops/monitoring.md                 # 食い違いのみ
docs/infra/terraform-design.md
docs/handoff.md
README.md                              # Phase 9 計画リンク
```

---

### Task 1: monitoring モジュール — 変数とダッシュボード

**Files:**
- Modify: `infra/modules/monitoring/variables.tf`, `main.tf`

**Behavior:**
- 変数追加: `http_api_id` (string), `lambda_function_names` (map(string) キー health/attendance/leave/users/exports), `db_instance_id` (string)
- `aws_cloudwatch_dashboard.overview` の body を更新:
  - API metrics (AWS/ApiGateway, ApiId)
  - Lambda metrics per function
  - RDS metrics (DBInstanceIdentifier = db_instance_id)
  - Log widgets for `/aws/lambda/<name>` ERROR filter（可能な範囲）
- SNS topic / email subscription は維持

- [ ] Commit: `feat(infra): expand CloudWatch dashboard widgets (W-270)`

---

### Task 2: アラーム

**Files:**
- Modify: `infra/modules/monitoring/main.tf`, `outputs.tf`（任意）

**Alarms → SNS:**
- Lambda Errors: each function, period 60, evaluation_periods 3, threshold 0, statistic Sum
- API 5XX: period 300, threshold 5
- API Latency p99: ExtendedStatistic p99, threshold 3000, period 300
- RDS CPU: > 80, period 300, evaluation 2 (≈10 min)
- RDS Connections: > 40, period 300, evaluation 2

HTTP API メトリクスの Namespace / MetricName は AWS ドキュメントに合わせる（`AWS/ApiGateway` の `5xx` / `Latency` 等。ApiId ディメンション）。

- [ ] Commit: `feat(infra): add CloudWatch alarms for Lambda API RDS (W-270)`

---

### Task 3: envs/dev 配線

**Files:**
- Modify: `infra/envs/dev/main.tf`

**Behavior:**
- `module.monitoring` に `http_api_id = module.api.http_api_id`, lambda map from api outputs, `db_instance_id = module.data.db_instance_id`
- monitoring ブロックを api / data の後に置くか、参照で暗黙依存

- [x] `cd infra/envs/dev && terraform fmt -recursive ../.. && terraform init -backend=false && terraform validate`
- [x] Commit: `feat(infra): wire monitoring module to api and rds (W-270)`

---

### Task 4: docs 同期

**Files:**
- Modify: `docs/infra/terraform-design.md`（monitoring 責務）, `docs/handoff.md`（次は W-109）, `README.md`（Phase 9 計画リンク）, `docs/ops/monitoring.md`（食い違いのみ）
- Do not edit `docs/wbs.md`

- [ ] Commit: `docs: sync Phase 9 monitoring polish and handoff (W-270)`
- [ ] Push `cursor/w270-monitoring-a099`

---

## 親が行うこと

- 設計レビュー → PR 更新、`docs/wbs.md` で W-270 完了
- apply は W-109 以降
