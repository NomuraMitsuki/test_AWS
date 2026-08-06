# Infra (Terraform)

`infra/envs/dev` が合成ルート。モジュールは `infra/modules/*`。

## AWS 認証（初回必須）

手順の詳細: [docs/infra/aws-auth-bootstrap.md](../docs/infra/aws-auth-bootstrap.md)

```bash
# 資格情報を設定したうえで
./infra/scripts/check-aws-auth.sh
```

OIDC ロールは初回 apply 後に初めて作られるため、**最初の plan/apply はローカル（または Cloud Agent）の一時資格情報**で行う。成功後に `terraform output gha_infra_role_arn` を GitHub Secrets `AWS_ROLE_ARN_INFRA` へ登録する。

## ローカル検証

```bash
cd infra/envs/dev
cp terraform.tfvars.example terraform.tfvars   # 必要なら編集
terraform init
terraform fmt -recursive ../..
terraform validate
# AWS 資格情報がある場合のみ（先に check-aws-auth.sh）
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
