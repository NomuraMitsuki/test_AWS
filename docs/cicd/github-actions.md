# CI/CD 設計 — GitHub Actions

## 方針

- AWS 認証は **OIDC**（アクセスキーを GitHub Secrets に置かない）
- `main` ブランチが `dev` 環境の正
- Terraform apply は plan 結果の確認後に手動承認（`environment: dev` 保護ルール）
- **品質ゲートは常に必須**。デプロイ／apply は Secret / Variable 未設定ならスキップ＋注記（workflow を赤にしない）。設定後の失敗はジョブ失敗とする
- job-level `if` では `secrets` コンテキストが使えないため、デプロイ系は gate ジョブで Secret 有無を `outputs` に渡し、後続ジョブを分岐する

## ワークフロー

### 1. `infra.yml` — Terraform

| トリガー | 現状（実装・W-260） | 目標（W-109 以降） |
|----------|---------------------|-------------------|
| PR（`infra/**`） | `fmt` / `validate` 必須。OIDC があれば `plan`（失敗時は注記のみ） | 同左＋ plan コメント投稿 |
| push to `main`（`infra/**`） | fmt + validate 必須。`AWS_ROLE_ARN_INFRA` があれば **plan → `environment: dev` → apply** 骨格。未設定はスキップ＋注記 | リモート state 利用・reviewers 必須化・実際の運用開始 |

権限: `github_oidc` モジュールが発行する `attendance-dev-gha-infra` ロール（必要最小の Terraform 権限へ後で絞る）。

**注意:** 現状ジョブは `terraform init -backend=false`。**リモート state 整備前は CI apply しない**（ローカル state のまま apply しない）。運用開始は W-109（Secrets・再 apply・リモート state）後。

### 2. `backend.yml` — Lambda

| トリガー | 現状（実装・W-260） | 目標（W-109 以降） |
|----------|---------------------|-------------------|
| PR（`backend/**`） | Python 3.12、`compileall` + `pytest`（必須） | 同左 |
| push to `main`（`backend/**`） | 同上＋ `AWS_ROLE_ARN_BACKEND` があれば zip → `lambda:UpdateFunctionCode`（health / attendance / leave / users / exports）。未設定はスキップ＋注記 | Secrets 登録後に実デプロイ |

権限: 対象 Lambda の更新と、必要なら S3 アーティファクトへの書込。

関数名デフォルト（repository variables で上書き可）:

| Variable | デフォルト |
|----------|-----------|
| `LAMBDA_HEALTH_NAME` | `attendance-dev-health` |
| `LAMBDA_ATTENDANCE_NAME` | `attendance-dev-attendance` |
| `LAMBDA_LEAVE_NAME` | `attendance-dev-leave` |
| `LAMBDA_USERS_NAME` | `attendance-dev-users` |
| `LAMBDA_EXPORTS_NAME` | `attendance-dev-exports` |

### 3. `frontend.yml` — Amplify / Next.js

| トリガー | 現状（実装・W-260） | 目標（後続） |
|----------|---------------------|-------------|
| PR（`frontend/**`） | `npm ci` / lint / `next build`（ダミー env 可）必須 | 同左 |
| push to `main`（`frontend/**`） | 同上＋任意で `aws amplify start-job`（`AMPLIFY_APP_ID` かつ `AWS_ROLE_ARN_INFRA` が必要。未設定はスキップ＋注記） | 専用 frontend OIDC ロールと `amplify:StartJob` 絞り込み（W-109 以降の IAM 整理） |

環境変数（Cognito User Pool ID、App Client ID、API Base URL）は Amplify 環境変数または GitHub Environments に保持。

**境界:** Terraform `amplify` モジュールの Hosting `enable_auto_build` が主経路。Actions の `start-job` は補助。認証は学習用に `AWS_ROLE_ARN_INFRA` を流用（`AWS_ROLE_ARN_BACKEND` は使わない）。

## ブランチ戦略（学習用）

```text
feature/*  →  PR  →  main (dev)
```

本番環境追加時は `release/*` や環境ディレクトリ追加で拡張する。

## 必要な GitHub 設定

1. **初回のみ**永続可能な実行環境の資格情報で `infra/envs/dev` を apply し、OIDC provider と IAM ロールを作成する（手順: [docs/infra/aws-auth-bootstrap.md](../infra/aws-auth-bootstrap.md)。state 保全に注意）
2. IAM ロールの信頼ポリシーで `repo:ORG/REPO:*` または `ref:refs/heads/main` に制限（モジュール既定）
3. Repository Environments: `dev` — apply ジョブで使用。reviewers 必須化は W-109 以降でよい
4. Secrets / Variables（**実登録は W-109**）:
   - Secret `AWS_ROLE_ARN_INFRA`（`terraform output gha_infra_role_arn`）— infra plan/apply および任意の Amplify `start-job`
   - Secret `AWS_ROLE_ARN_BACKEND`（`terraform output gha_backend_role_arn`）— Lambda 更新
   - Variable `AWS_REGION=ap-northeast-1`（または workflow 既定）
   - Variable `AMPLIFY_APP_ID`（任意）— `amplify start-job`
   - Variable `LAMBDA_*_NAME`（任意）— 関数名上書き
   - Amplify / Cognito 関連（フロント用）

## 品質ゲート（最小）

- Terraform: fmt + validate 必須、plan 差分を PR で確認（Secret 依存）
- Backend: `compileall` + pytest グリーン
- Frontend: `next build` 成功

## ロールバック

- infra: 直前の state に対する再 apply、または destroy/再構築（学習環境）
- Lambda: 前バージョンの `publish` / alias（初期は手動で前 zip を再デプロイでも可）
- Frontend: Amplify の前ジョブ再デプロイ
