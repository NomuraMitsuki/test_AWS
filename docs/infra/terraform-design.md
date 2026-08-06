# Terraform 設計

## 目的

勤怠管理アプリの AWS リソースをコード化し、再現可能な `dev` 環境を構築する。後から staging / prod を追加できるようモジュール分割する。

## ディレクトリ構成（予定）

```text
infra/
  envs/
    dev/
      main.tf
      variables.tf
      outputs.tf
      terraform.tfvars
      backend.tf
  modules/
    network/      # VPC, subnets, NAT, SG
    cognito/      # User Pool, groups, app client
    data/         # RDS, Secrets Manager, subnet group
    storage/      # S3 exports bucket
    api/          # HTTP API, JWT authorizer, Lambda, IAM
    monitoring/   # Log groups, alarms, dashboard
    github_oidc/  # GitHub Actions OIDC provider + roles
```

## モジュール責務

| モジュール | 主要リソース |
|------------|--------------|
| network | VPC, public/private subnets (2 AZ), IGW, NAT Gateway×1, route tables, Lambda SG, RDS SG |
| cognito | User Pool（セルフサインアップ無効）, Groups, App Client, Domain（任意） |
| data | RDS PostgreSQL `db.t4g.micro`, Secrets Manager, parameter group |
| storage | S3 bucket, Block Public Access, lifecycle（任意） |
| api | Lambda×4+, HTTP API, routes, JWT authorizer, IAM roles, VPC config |
| monitoring | CloudWatch ダッシュボード骨格、SNS（アラーム本体は Phase 後半 / W-270） |
| github_oidc | OIDC provider, deploy roles（infra / backend。frontend は Amplify 連携時に追加） |

## State 管理

- リモート state: S3 + DynamoDB ロック（初回のみ手動または bootstrap スクリプト）
- key 例: `attendance/dev/terraform.tfstate`
- ローカル検証時は `backend "local"` に切り替え可能

## 主要変数

| 変数 | 例 | 説明 |
|------|-----|------|
| project_name | `attendance` | リソース名プレフィックス |
| environment | `dev` | 環境名 |
| aws_region | `ap-northeast-1` | |
| db_instance_class | `db.t4g.micro` | |
| amplify_app_id / branch | （後から） | CORS オリジン解決用 |
| github_org_repo | `owner/repo` | OIDC 信頼条件 |

## セキュリティ方針

- RDS はプライベートサブネットのみ。パブリックアクセス無効
- Lambda → RDS は SG で 5432 のみ
- DB パスワードは Secrets Manager で自動生成・ローテーションは後続課題
- 長期 AWS キーをリポジトリに置かない（OIDC）
- 初回 apply 用の一時資格情報と OIDC 切り替え手順: [aws-auth-bootstrap.md](aws-auth-bootstrap.md)

## デプロイ順序

1. bootstrap（state 用 S3/DynamoDB）— 必要なら
2. `network` → `cognito` → `data` → `storage`
3. `api`（Lambda コードの初回はプレースホルダ可）
4. `monitoring` / `github_oidc`
5. Amplify アプリは Terraform またはコンソール＋ドキュメント連携

## コスト抑制メモ

- NAT Gateway は 1 つ（AZ 冗長なし）
- RDS Multi-AZ オフ、バックアップ保持は短め（例: 7 日）
- 学習終了時は `terraform destroy` を前提にタグ `Project=attendance` を付与
