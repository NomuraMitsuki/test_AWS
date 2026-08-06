# Infra (Terraform)

`infra/envs/dev` が合成ルート。モジュールは `infra/modules/*`。

## ローカル検証

```bash
cd infra/envs/dev
cp terraform.tfvars.example terraform.tfvars   # 必要なら編集
terraform init
terraform fmt -recursive ../..
terraform validate
# AWS 資格情報がある場合のみ
terraform plan
```

初回 apply 前に、GitHub Secrets に `AWS_ROLE_ARN_INFRA` を設定する（OIDC ロールは apply 後に出力されるため、最初の apply はローカル資格情報でも可）。

## モジュール

| モジュール | 内容 |
|------------|------|
| network | VPC / サブネット / NAT×1 / Lambda・RDS SG |
| cognito | User Pool（招待のみ）/ groups / app client |
| data | RDS PostgreSQL + Secrets Manager |
| storage | exports 用 S3（公開禁止） |
| monitoring | SNS + CloudWatch ダッシュボード骨格 |
| github_oidc | GitHub Actions OIDC ロール |
