# Phase 8 CI/CD Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本リポジトリでは親が `implementation-worker` に本計画全体を委譲してもよい。

**Goal:** `backend.yml` 新設、`frontend.yml` の任意 Amplify `start-job`、`infra.yml` の main 向け plan→apply 骨格を実装し、docs を同期する（Secrets 実登録・apply なし）。

**Architecture:** 品質ゲート（validate / pytest / lint-build）は必須。デプロイ系は Secret / Variable 未設定ならジョブをスキップ＋注記し、設定後は失敗を失敗として扱う。Amplify `start-job` は `AWS_ROLE_ARN_INFRA` を流用。

**Tech Stack:** GitHub Actions, Python 3.12, AWS OIDC, Amplify CLI via AWS CLI, Terraform 1.9.8

## Global Constraints

- apply / Secrets 実登録をしない。W-109 / W-270 に触れない
- スペック: [docs/superpowers/specs/2026-08-07-phase8-cicd-workflows-design.md](../specs/2026-08-07-phase8-cicd-workflows-design.md)
- CI 正本: [docs/cicd/github-actions.md](../../cicd/github-actions.md)
- `docs/wbs.md` ステータスは触らない（親が更新）
- PR 操作しない。ブランチ `cursor/w260-cicd-a099` で push
- 関数名デフォルト: `attendance-dev-{health,attendance,leave,users,exports}`（`name_prefix` と一致）。vars で上書き可

## File structure

```text
.github/workflows/backend.yml          # 新規
.github/workflows/frontend.yml         # start-job 追加
.github/workflows/infra.yml            # main apply 骨格
docs/cicd/github-actions.md            # 現状＝W-260
docs/handoff.md
README.md                              # Phase 8 計画リンク
```

---

### Task 1: `backend.yml`

**Files:**
- Create: `.github/workflows/backend.yml`

**Behavior:**
- PR / push on `backend/**` and workflow file
- Job `test`: Python 3.12, `pip install -r` 各関数の requirements + pytest, `python -m compileall backend`, `pytest backend/tests`
- Job `deploy` (push main only): `if: ${{ secrets.AWS_ROLE_ARN_BACKEND != '' }}`。未設定時は別ジョブまたは step で注記のみ（workflow を赤にしない）
- deploy: OIDC → 各ディレクトリを zip（requirements を同梱する簡易スクリプト可）→ `aws lambda update-function-code`
- 関数名: `vars.LAMBDA_HEALTH_NAME` 等、デフォルト `attendance-dev-health` など

- [ ] ローカル: `cd /workspace && python -m compileall backend && pytest backend/tests` グリーン
- [ ] Commit: `ci: add backend.yml with pytest and optional Lambda deploy (W-260)`

---

### Task 2: `frontend.yml` Amplify start-job

**Files:**
- Modify: `.github/workflows/frontend.yml`

**Behavior:**
- 既存 lint-build 維持
- Job `amplify-job` (push main only): `if: ${{ vars.AMPLIFY_APP_ID != '' && secrets.AWS_ROLE_ARN_INFRA != '' }}`
- OIDC with `AWS_ROLE_ARN_INFRA` → `aws amplify start-job --app-id ... --branch-name main --job-type RELEASE`
- 条件非該当時はスキップ（必須ゲートは lint-build のみ）

- [ ] Commit: `ci: add optional Amplify start-job on frontend main (W-260)`

---

### Task 3: `infra.yml` main plan → apply 骨格

**Files:**
- Modify: `.github/workflows/infra.yml`

**Behavior:**
- validate 必須のまま
- PR plan: 現状維持（Secret 無し時注記）
- 新規 job `apply` (push main only):
  - `if: ${{ secrets.AWS_ROLE_ARN_INFRA != '' }}` — 未設定ならスキップ＋注記ジョブ
  - `environment: dev`
  - OIDC → init → plan → apply（`-auto-approve` は environment 承認後。学習用骨格）
  - Secret 設定後の失敗はジョブ失敗（continue-on-error しない）
  - コメント／docs で「リモート state 整備前は CI apply しない」と注意

- [ ] Commit: `ci: add infra main apply skeleton with environment dev (W-260)`

---

### Task 4: docs 同期

**Files:**
- Modify: `docs/cicd/github-actions.md`（現状＝W-260 実装、目標の残があれば W-109 以降）
- Modify: `docs/handoff.md`（次は W-109 / W-270）
- Modify: `README.md`（Phase 8 計画リンク）
- Do not edit `docs/wbs.md`

- [ ] Commit: `docs: sync Phase 8 CI/CD workflows and handoff (W-260)`
- [ ] Push `cursor/w260-cicd-a099`

---

## 親が行うこと

- 設計レビュー → PR 更新、`docs/wbs.md` で W-260 完了
- Secrets 登録は W-109
