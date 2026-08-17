# CI/CD 設計 — GitHub Actions

## 方針

- AWS 認証は **OIDC**（アクセスキーを GitHub Secrets に置かない）
- `main` ブランチが `dev` 環境の正
- Terraform apply は `environment: dev` 保護ルールで **ジョブ開始前**に手動承認（**reviewers 必須**。承認後に plan → apply。plan を見てから承認する流れではない）。GitHub Free の private リポジトリでは Required reviewers が使えないことがあり、その場合は `main` の infra push で apply が自動実行される（本学習リポジトリは受容済み）
- **品質ゲートは常に必須**。デプロイ／apply は Secret / Variable 未設定ならスキップ＋注記（workflow を赤にしない）。設定後の失敗はジョブ失敗とする（`continue-on-error` で握りつぶさない）
- job-level `if` では `secrets` コンテキストが使えないため、デプロイ系は gate ジョブで Secret 有無を `outputs` に渡し、後続ジョブを分岐する

## ワークフロー

### 1. `infra.yml` — Terraform

| トリガー | 現状（W-109） |
|----------|----------------|
| PR（`infra/**`） | `fmt` / `validate` 必須（`terraform init -backend=false`）。**plan-gate**: `AWS_ROLE_ARN_INFRA` が空なら plan をスキップ＋注記。Secret ありなら OIDC → `terraform init -backend-config=backend.hcl` → plan（失敗はジョブ失敗） |
| push to `main`（`infra/**`） | fmt + validate 必須。`AWS_ROLE_ARN_INFRA` があれば `environment: dev` → OIDC → 同上 init → plan → apply。Required reviewers は付けられるプランなら必須。本リポジトリ（private + Free）は未設定のため apply は自動。Secret 未設定はスキップ＋注記 |

権限: `github_oidc` モジュールが発行する `attendance-dev-gha-infra` ロール（必要最小の Terraform 権限へ後で絞る）。

本体 state は S3 + DynamoDB（`infra/bootstrap` が作成。`backend.hcl` をコミット）。validate だけは backend に接続しない。手順の正本: [docs/infra/aws-auth-bootstrap.md](../infra/aws-auth-bootstrap.md)。

### 2. `backend.yml` — Lambda

| トリガー | 現状（実装・W-260） | 目標（Secrets 登録後） |
|----------|---------------------|-------------------|
| PR（`backend/**`） | Python 3.12、`compileall` + `pytest`（必須） | 同左 |
| push to `main`（`backend/**`） | 同上＋ `AWS_ROLE_ARN_BACKEND` があれば zip → `lambda:UpdateFunctionCode`（health / attendance / leave / users / exports / migrate）。migrate の zip には `backend/migrations/*.sql` を同梱。未設定はスキップ＋注記 | Secrets 登録後に実デプロイ |

権限: 対象 Lambda の更新と、必要なら S3 アーティファクトへの書込。

関数名デフォルト（repository variables で上書き可）:

| Variable | デフォルト |
|----------|-----------|
| `LAMBDA_HEALTH_NAME` | `attendance-dev-health` |
| `LAMBDA_ATTENDANCE_NAME` | `attendance-dev-attendance` |
| `LAMBDA_LEAVE_NAME` | `attendance-dev-leave` |
| `LAMBDA_USERS_NAME` | `attendance-dev-users` |
| `LAMBDA_EXPORTS_NAME` | `attendance-dev-exports` |
| `LAMBDA_MIGRATE_NAME` | `attendance-dev-migrate` |

### 3. `frontend.yml` — Amplify / Next.js

| トリガー | 現状（実装・W-260） | 目標（後続） |
|----------|---------------------|-------------|
| PR（`frontend/**`） | `npm ci` / lint / `next build`（ダミー env 可）必須 | 同左 |
| push to `main`（`frontend/**`） | 同上＋任意で `aws amplify start-job`（`AMPLIFY_APP_ID` かつ `AWS_ROLE_ARN_INFRA` が必要。未設定はスキップ＋注記） | 専用 frontend OIDC ロールと `amplify:StartJob` 絞り込み（後続の IAM 整理） |

環境変数（Cognito User Pool ID、App Client ID、API Base URL）は Amplify 環境変数または GitHub Environments に保持。

**境界:** Terraform `amplify` モジュールの Hosting `enable_auto_build` が主経路。Actions の `start-job` は補助。認証は学習用に `AWS_ROLE_ARN_INFRA` を流用（`AWS_ROLE_ARN_BACKEND` は使わない）。Amplify GitHub 接続は任意（トークン空なら Hosting 連携は後回し）。

## ブランチ戦略（学習用）

```text
feature/*  →  PR  →  main (dev)
```

本番環境追加時は `release/*` や環境ディレクトリ追加で拡張する。

## 必要な GitHub 設定

1. **Mac** で `infra/bootstrap` を apply し、`backend.hcl` をコミットしたうえで `infra/envs/dev` を apply する（手順: [docs/infra/aws-auth-bootstrap.md](../infra/aws-auth-bootstrap.md)）。Cloud Agent では apply しない
2. IAM ロールの信頼ポリシーで `repo:ORG/REPO:*` または `ref:refs/heads/main` に制限（モジュール既定）
3. Repository Environments: `dev` — apply ジョブで使用。Required reviewers は付けられるプランなら必須（学習用 1 人可）。GitHub Free の private では使えないことがあり、本リポジトリは未設定（`main` の infra push で apply が自動）
4. Secrets / Variables（**実登録はユーザーの Mac**。エージェントは `gh secret set` しない）:
   - Secret `AWS_ROLE_ARN_INFRA`（`terraform output gha_infra_role_arn`）— infra plan/apply および任意の Amplify `start-job`
   - Secret `AWS_ROLE_ARN_BACKEND`（`terraform output gha_backend_role_arn`）— Lambda 更新
   - リージョンは workflow 既定 `ap-northeast-1`（Secret 不要）
   - Variable `AMPLIFY_APP_ID`（任意）— `amplify start-job`
   - Variable `LAMBDA_*_NAME`（任意）— 関数名上書き
   - Amplify / Cognito 関連（フロント用）

## 品質ゲート（最小）

- Terraform: fmt + validate 必須、plan 差分を PR で確認（Secret 依存。空ならスキップ＋注記）
- Backend: `compileall` + pytest グリーン
- Frontend: `next build` 成功

## ロールバック

- infra: 直前の **リモート state** に対する再 apply、または本体の destroy/再構築（学習環境）。bootstrap（state 用 S3 / DynamoDB）は残す
- Lambda: 前バージョンの `publish` / alias（初期は手動で前 zip を再デプロイでも可）
- Frontend: Amplify の前ジョブ再デプロイ
