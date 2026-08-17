# Phase 10 — リモート state・GitHub Secrets・CI plan 有効化設計（W-109）

**日付**: 2026-08-17  
**ステータス**: Approved（エージェントは apply / Secrets 実登録をしない）  
**WBS**: W-109  
**手順正本**: [docs/infra/aws-auth-bootstrap.md](../../infra/aws-auth-bootstrap.md)  
**CI 正本**: [docs/cicd/github-actions.md](../../cicd/github-actions.md)

## 1. ゴール

Terraform の **リモート state（S3 + DynamoDB）** をコード化し、`infra.yml` の plan / apply が backend を使えるようにする。本体 apply と GitHub Secrets 登録は **ユーザーの Mac** で行い、Cloud Agent では実行しない（エフェメラル環境で state を失うため）。

完了条件（リポジトリ側）: bootstrap / `envs/dev` backend / CI 配線 / 手順書が揃い、`terraform validate` が通る。  
完了条件（運用側・ユーザー）: Mac で bootstrap → 本体 apply → Secrets 登録。

## 2. 非ゴール

- エージェントからの `terraform apply` / `gh secret set`
- IAM の最小権限への本格絞り込み
- Amplify GitHub 接続の必須化（トークンは任意。空なら Hosting 連携は後回し）
- Environment `dev` の reviewers 必須化（任意。後から可）

## 3. 方針（採用案 A）

独立した `infra/bootstrap` で state 用バケットとロックテーブルだけを作る（このディレクトリの state はローカル可。**destroy しない**）。その後 `infra/envs/dev` の `backend "s3"` を有効化し、本体スタックをリモート state で管理する。

## 4. 作業順序（Mac）

認証は `aws login` + `./infra/scripts/tf-dev.sh`（`export-credentials`）。

1. `infra/bootstrap` を apply（S3 + DynamoDB）
2. `infra/envs/dev` で `terraform init`（S3 backend）
3. `./infra/scripts/tf-dev.sh apply`（本体。RDS / Cognito / API / monitoring / OIDC 等）
4. `terraform output gha_infra_role_arn` / `gha_backend_role_arn` を控える
5. GitHub Secrets: `AWS_ROLE_ARN_INFRA` / `AWS_ROLE_ARN_BACKEND`（必要なら `AWS_REGION=ap-northeast-1`）
6. Repository Environment `dev`（apply ジョブ用。reviewers は任意）
7. Amplify を接続した場合: `amplify_default_branch_url` を `cors_amplify_origin` に入れて再 apply（循環回避は現状どおり）

## 5. コード

### 5.1 `infra/bootstrap`

- S3: versioning、SSE、Block Public Access。bucket 名はグローバル衝突回避のため **アカウント ID を含める**（例: `attendance-tfstate-dev-<account_id>`）
- DynamoDB: lock 用テーブル（例: `attendance-tfstate-lock-dev`）
- 出力: bucket 名、table 名（`envs/dev` の backend と docs に転記）

### 5.2 `infra/envs/dev/providers.tf`

- コメントアウトしていた `backend "s3"` を有効化
- key: `attendance/dev/terraform.tfstate`
- region: `ap-northeast-1`
- bucket / dynamodb_table は bootstrap 出力と一致させる（ハードコードするか `backend.hcl` で渡す。validate 可能な形にする）

### 5.3 `infra.yml`

| ジョブ | init |
|--------|------|
| validate | `-backend=false` のまま（Secrets / bucket 未作成でも品質ゲートが通る） |
| PR plan / main apply | `terraform init`（backend あり）。OIDC。Secret 未設定時は現状どおりスキップ＋注記 |

apply ジョブの「リモート state 前は CI apply しない」注意は、backend 有効化後に「運用開始は Secrets 登録と bootstrap 完了後」へ更新する。

## 6. 検証

- `infra/bootstrap` と `infra/envs/dev`: `terraform fmt` / `init -backend=false` / `validate`
- docs: [aws-auth-bootstrap.md](../../infra/aws-auth-bootstrap.md) §D を本 Phase の手順に更新、[github-actions.md](../../cicd/github-actions.md)、handoff、WBS
- apply / Secrets 実登録はユーザー作業（手順に `gh secret set` 例を書いてよい。エージェントは実行しない）

## 7. 完了後

- WBS W-109 を、コード完了と「ユーザー apply / Secrets 待ち」が区別できるメモにする（親がステータス確定）
- 次: ユーザーが Mac で apply したあと、実 Cognito ログインや CI plan の確認
