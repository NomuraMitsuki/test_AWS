# CI/CD 設計 — GitHub Actions

## 方針

- AWS 認証は **OIDC**（アクセスキーを GitHub Secrets に置かない）
- `main` ブランチが `dev` 環境の正
- Terraform apply は plan 結果の確認後に手動承認（`environment` 保護ルール）

## ワークフロー

### 1. `infra.yml` — Terraform

| トリガー | 現状（実装） | 目標（後続） |
|----------|--------------|--------------|
| PR（`infra/**`） | `fmt` / `validate`。OIDC があれば `plan`（失敗時は注記のみ） | 同左＋ plan コメント投稿 |
| push to `main`（`infra/**`） | validate のみ（apply ジョブ未実装） | plan → **environment: dev の approval** → apply |

権限: `github_oidc` モジュールが発行する `attendance-dev-gha-infra` ロール（必要最小の Terraform 権限へ後で絞る）。現状ジョブは `terraform init -backend=false` のため、リモート state 化後に backend 利用へ切り替える。
### 2. `backend.yml` — Lambda

| トリガー | 内容 |
|----------|------|
| PR（`backend/**`） | lint / 単体テスト（pytest） |
| push to `main`（`backend/**`） | パッケージ zip またはコンテナビルド → `aws lambda update-function-code`（関数ごと） |

権限: 対象 Lambda の更新と、必要なら S3 アーティファクトへの書込。

### 3. `frontend.yml` — Amplify / Next.js

| トリガー | 内容 |
|----------|------|
| PR（`frontend/**`） | `npm ci` / lint / build |
| push to `main`（`frontend/**`） | Amplify へ連携（Amplify の GitHub 接続を主、または Actions から `amplify start-job`） |

環境変数（Cognito User Pool ID、App Client ID、API Base URL）は Amplify 環境変数または GitHub Environments に保持。

## ブランチ戦略（学習用）

```text
feature/*  →  PR  →  main (dev)
```

本番環境追加時は `release/*` や環境ディレクトリ追加で拡張する。

## 必要な GitHub 設定

1. **初回のみ**永続可能な実行環境の資格情報で `infra/envs/dev` を apply し、OIDC provider と IAM ロールを作成する（手順: [docs/infra/aws-auth-bootstrap.md](../infra/aws-auth-bootstrap.md)。state 保全に注意）
2. IAM ロールの信頼ポリシーで `repo:ORG/REPO:*` または `ref:refs/heads/main` に制限（モジュール既定）
3. Repository Environments: `dev` — 現状ワークフローは plan までのため任意。apply ジョブ追加時は reviewers を必須にする
4. Secrets / Variables:
   - `AWS_ROLE_ARN_INFRA`（`terraform output gha_infra_role_arn`）
   - `AWS_ROLE_ARN_BACKEND`（`terraform output gha_backend_role_arn`）
   - `AWS_REGION=ap-northeast-1`
   - Amplify / Cognito 関連（フロント用）

## 品質ゲート（最小）

- Terraform: fmt + validate 必須、plan 差分を PR で確認
- Backend: pytest グリーン
- Frontend: `next build` 成功

## ロールバック

- infra: 直前の state に対する再 apply、または destroy/再構築（学習環境）
- Lambda: 前バージョンの `publish` / alias（初期は手動で前 zip を再デプロイでも可）
- Frontend: Amplify の前ジョブ再デプロイ
