# Infra (Terraform)

`infra/envs/dev` が合成ルート。モジュールは `infra/modules/*`。

## AWS 認証（初回必須）

手順の詳細: [docs/infra/aws-auth-bootstrap.md](../docs/infra/aws-auth-bootstrap.md)

```bash
# 推奨: aws login（必要時）+ export-credentials + terraform を一括
./infra/scripts/tf-dev.sh auth
./infra/scripts/tf-dev.sh plan
./infra/scripts/tf-dev.sh apply   # 再 plan のあと [y/N]（課金リソースに注意）

# AWS CLI の疎通確認のみ（Terraform 用 export は別途）
./infra/scripts/check-aws-auth.sh
```

`aws login` だけだと Terraform が資格情報を拾えないことがある。`tf-dev.sh` は `aws configure export-credentials` を挟んで回避する。`apply` は保存済み plan を使うため Terraform 標準の yes/no は出ず、スクリプトが `[y/N]` を聞く。

OIDC ロールは初回 apply 後に初めて作られるため、**最初の plan/apply はローカル等の一時資格情報**で行う（state はローカルのままなので、永続環境で apply するか先にリモート state 化する。詳細は認証手順）。成功後に次を GitHub Secrets へ登録する:

- `AWS_ROLE_ARN_INFRA` ← `terraform output gha_infra_role_arn`
- `AWS_ROLE_ARN_BACKEND` ← `terraform output gha_backend_role_arn`

## ローカル検証

```bash
# 一括（推奨）
./infra/scripts/tf-dev.sh plan

# または手動
cd infra/envs/dev
cp terraform.tfvars.example terraform.tfvars   # 必要なら編集
eval "$(aws configure export-credentials --format env)"   # aws login 利用時
terraform init
terraform fmt -recursive ../..
terraform validate
terraform plan
```

## モジュール

| モジュール | 内容 |
|------------|------|
| network | VPC / サブネット / NAT×1 / Lambda・RDS SG |
| cognito | User Pool（招待のみ）/ groups / app client |
| data | RDS PostgreSQL + Secrets Manager |
| storage | exports 用 S3（公開禁止） |
| monitoring | SNS + CloudWatch ダッシュボード骨格 |
| github_oidc | GitHub Actions OIDC ロール |
| api | HTTP API / Cognito JWT authorizer / health Lambda（`GET /health` は認証なし）/ attendance・leave Lambda（VPC 内・JWT 必須ルート） |
