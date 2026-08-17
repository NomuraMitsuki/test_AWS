# Phase 10 W-109 Remote State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本リポジトリでは親が `implementation-worker` に本計画全体を委譲してもよい。

**Goal:** `infra/bootstrap`（S3 + DynamoDB lock）、`envs/dev` の S3 backend、`infra.yml` の remote init、手順書を実装し terraform validate を通す。apply / Secrets 実登録はしない。

**Architecture:** bootstrap は独立スタック（ローカル state、destroy しない）。本体は `backend "s3" {}` + コミットする `backend.hcl`。CI validate は `-backend=false`。plan/apply は Secret ありのときだけ `init -backend-config=backend.hcl`。

**Tech Stack:** Terraform 1.9.x, AWS S3/DynamoDB backend, GitHub Actions OIDC

## Global Constraints

- エージェントは `terraform apply` / `gh secret set` をしない
- スペック: [docs/superpowers/specs/2026-08-17-phase10-w109-remote-state-design.md](../specs/2026-08-17-phase10-w109-remote-state-design.md)
- `docs/wbs.md` ステータスの確定更新は親（コード完了とユーザー apply 待ちをメモ可。ステータスは親）
- PR 操作しない。ブランチ `cursor/w109-remote-state-a099`
- `tf-dev.sh` は本体 `infra/envs/dev` 専用のまま

## File structure

```text
infra/bootstrap/{main.tf,outputs.tf,providers.tf,README.md}
infra/envs/dev/providers.tf          # backend "s3" 部分設定
infra/envs/dev/backend.hcl.example
infra/envs/dev/backend.hcl           # example と同型のプレースホルダ可（CI init 用。実名はユーザーが上書きコミット）
.github/workflows/infra.yml
docs/infra/aws-auth-bootstrap.md
docs/cicd/github-actions.md
docs/infra/terraform-design.md
docs/handoff.md
infra/README.md
```

`backend.hcl` を gitignore しない。初回コミットは example と同じプレースホルダでよい（bucket 未作成時は Secret 未設定なら plan スキップ）。

---

### Task 1: `infra/bootstrap`

**Files:**
- Create: `infra/bootstrap/providers.tf`（local backend、aws provider `ap-northeast-1`）
- Create: `infra/bootstrap/main.tf` — data.aws_caller_identity、S3 bucket `attendance-tfstate-dev-${account_id}`（versioning, sse aes256, public access block）、DynamoDB `attendance-tfstate-lock-dev`（LockID HASH）
- Create: `infra/bootstrap/outputs.tf` — bucket_name, dynamodb_table_name
- Create: `infra/bootstrap/README.md` — init/apply、destroy しない、出力を backend.hcl へ

- [x] `cd infra/bootstrap && terraform fmt && terraform init -backend=false && terraform validate`
- [x] Commit: `feat(infra): add tfstate S3 and DynamoDB bootstrap (W-109)`

---

### Task 2: `envs/dev` S3 backend

**Files:**
- Modify: `infra/envs/dev/providers.tf` — コメントの backend を外し、部分設定:

```hcl
backend "s3" {
  key    = "attendance/dev/terraform.tfstate"
  region = "ap-northeast-1"
  encrypt = true
}
```

- Create: `infra/envs/dev/backend.hcl.example` と `backend.hcl`:

```hcl
bucket         = "REPLACE_AFTER_BOOTSTRAP"
dynamodb_table = "attendance-tfstate-lock-dev"
```

- Modify: `infra/scripts/tf-dev.sh` — `init` 時に `-backend-config=backend.hcl` を使う（apply/plan がリモートを向く）。ファイルがプレースホルダのままでも、ユーザーが実名に差し替えるまで Mac apply は失敗してよい。スクリプト先頭コメントで bootstrap 非対象と明記。

- [x] `cd infra/envs/dev && terraform init -backend=false && terraform validate`
- [x] Commit: `feat(infra): enable S3 backend config for envs/dev (W-109)`

---

### Task 3: `infra.yml` plan/apply を remote init に

**Files:**
- Modify: `.github/workflows/infra.yml`

**Behavior:**
- validate: 現状どおり `init -backend=false`
- PR plan: **plan-gate**（Secret 空なら skip-note。validate は必須）。Secret あり: OIDC → `terraform init -backend-config=backend.hcl` → plan。continue-on-error しない
- apply: Secret 空なら skip。あり: `environment: dev` → OIDC → 同上 init（`-backend=false` 削除）→ plan → apply
- コメントを W-109 手順に更新

- [x] Commit: `ci: use remote terraform backend for plan and apply (W-109)`

---

### Task 4: 手順書同期

**Files:**
- Rewrite/update: `docs/infra/aws-auth-bootstrap.md` — Cloud Agent apply 禁止。§C Mac + bootstrap コマンド。§D をスペック §4 に置換（手作り bucket + migrate を捨てる）。`gh secret set` 例。Environment reviewers 必須。apply 後の残作業（初回 admin、migrations）は短く案内
- Update: `docs/cicd/github-actions.md` — 現状＝remote backend + gate。apply は reviewers 必須
- Update: `docs/infra/terraform-design.md` — bootstrap ディレクトリ、State は S3、destroy は本体のみ
- Update: `infra/README.md`、`docs/handoff.md`（次はユーザー Mac apply）
- Do not set WBS ステータス完了（親）。メモの食い違いだけ直してよいがステータスは触らない方が安全 → **wbs.md は触らない**

- [x] Commit: `docs: rewrite W-109 remote state and Secrets procedure`
- [x] Push `cursor/w109-remote-state-a099`

---

## 親が行うこと

- 設計レビュー → PR 更新、WBS を「コード完了・ユーザー apply 待ち」に
- apply / Secrets はユーザー
