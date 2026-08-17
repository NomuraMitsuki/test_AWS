# Infra (Terraform)

`infra/envs/dev` が合成ルート。モジュールは `infra/modules/*`。state 用バケットは `infra/bootstrap`（本体とは独立。**destroy しない**）。

## AWS 認証（初回必須）

手順の詳細: [docs/infra/aws-auth-bootstrap.md](../docs/infra/aws-auth-bootstrap.md)

**Cloud Agent では apply しない。** 次はユーザーの Mac で bootstrap → `backend.hcl` コミット → 本体 apply → Secrets。

```bash
# 1) state 用 S3 / DynamoDB（tf-dev.sh は使わない）
cd infra/bootstrap
eval "$(aws configure export-credentials --format env)"  # aws login 利用時
terraform init
terraform apply
# 出力を infra/envs/dev/backend.hcl に書いてコミット

# 2) 本体（推奨: aws login + export-credentials + terraform を一括）
./infra/scripts/tf-dev.sh auth
./infra/scripts/tf-dev.sh plan
./infra/scripts/tf-dev.sh apply   # 再 plan のあと [y/N]（課金リソースに注意）

# AWS CLI の疎通確認のみ（Terraform 用 export は別途）
./infra/scripts/check-aws-auth.sh
```

`aws login` だけだと Terraform が資格情報を拾えないことがある。`tf-dev.sh` は `aws configure export-credentials` を挟んで回避する。`apply` は保存済み plan を使うため Terraform 標準の yes/no は出ず、スクリプトが `[y/N]` を聞く。`tf-dev.sh` は **本体専用**（bootstrap 非対象）。init は `-backend-config=backend.hcl` を使う。

apply 後の RDS マイグレーションと初回 admin は `./infra/scripts/invoke-migrate.sh`（**apply はしない**）。手順の正本: [docs/infra/aws-auth-bootstrap.md](../docs/infra/aws-auth-bootstrap.md) §E。

OIDC ロールは本体の初回 apply 後に初めて作られる。成功後に次を GitHub Secrets へ登録する（エージェントは `gh secret set` しない）:

- `AWS_ROLE_ARN_INFRA` ← `terraform output gha_infra_role_arn`
- `AWS_ROLE_ARN_BACKEND` ← `terraform output gha_backend_role_arn`

Repository Environment `dev` は **reviewers 必須**。

## ローカル検証

```bash
# bootstrap（apply は Mac。validate はローカル可）
cd infra/bootstrap
terraform fmt -check
terraform init -backend=false
terraform validate

# 本体
cd infra/envs/dev
cp terraform.tfvars.example terraform.tfvars   # 必要なら編集
terraform fmt -check -recursive ../..
terraform init -backend=false
terraform validate

# 資格情報付き plan（backend.hcl に実名を書いたあと）
./infra/scripts/tf-dev.sh plan
```

## モジュール

| モジュール | 内容 |
|------------|------|
| network | VPC / サブネット / NAT×1 / Lambda・RDS SG |
| cognito | User Pool（招待のみ）/ groups / app client |
| data | RDS PostgreSQL + Secrets Manager |
| storage | exports 用 S3（公開禁止） |
| monitoring | SNS + CloudWatch ダッシュボード（API / Lambda×5 / RDS）。migrate は Errors アラームのみ |
| github_oidc | GitHub Actions OIDC ロール |
| api | HTTP API / Cognito JWT authorizer / health Lambda（`GET /health` は認証なし）/ attendance・leave・users・exports Lambda（VPC 内・JWT 必須ルート。exports は S3 Put/Presign IAM）/ migrate Lambda（VPC 内・HTTP 非公開）/ CORS（`cors_allow_origins`） |
| amplify | Amplify Hosting（Next.js / `frontend`）。Cognito・API URL を環境変数で渡す。GitHub トークンは sensitive（空でも validate 可） |

## フロント（ローカル）

```bash
cd frontend
cp .env.example .env.local   # Cognito / API URL を記入（コミットしない）
npm ci
npm run dev
```

Cognito / API なしの画面確認は `cd frontend && npm run dev:demo`（[frontend/README.md](../frontend/README.md)）。**Amplify には `NEXT_PUBLIC_DEMO_MODE` を設定しない。**

API CORS は `cors_allow_localhost=true`（既定）で `http://localhost:3000` を許可。Amplify オリジンは apply 後に `terraform output amplify_default_branch_url` を `cors_amplify_origin` へ設定する（循環依存回避）。
