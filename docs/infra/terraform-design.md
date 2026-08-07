# Terraform 設計

## 目的

勤怠管理アプリの AWS リソースをコード化し、再現可能な `dev` 環境を構築する。後から staging / prod を追加できるようモジュール分割する。

## ディレクトリ構成

```text
infra/
  envs/
    dev/
      main.tf
      variables.tf
      outputs.tf
      providers.tf          # required_providers + backend（現状は local、S3 はコメント）
      terraform.tfvars
  modules/
    network/      # VPC, subnets, NAT, SG
    cognito/      # User Pool, groups, app client
    data/         # RDS, Secrets Manager, subnet group
    storage/      # S3 exports bucket
    api/          # HTTP API, JWT authorizer, Lambda, IAM, CORS
    amplify/      # Amplify Hosting app + branch（Next.js / frontend）
    monitoring/   # Log groups, alarms, dashboard
    github_oidc/  # GitHub Actions OIDC provider + roles
  scripts/
    check-aws-auth.sh
    tf-dev.sh           # aws login + export-credentials + plan/apply
```

## モジュール責務

| モジュール | 主要リソース |
|------------|--------------|
| network | VPC, public/private subnets (2 AZ), IGW, NAT Gateway×1, route tables, Lambda SG, RDS SG |
| cognito | User Pool（セルフサインアップ無効）, Groups, App Client, Domain（任意） |
| data | RDS PostgreSQL `db.t4g.micro`, Secrets Manager, parameter group |
| storage | S3 bucket, Block Public Access, lifecycle（任意） |
| api | HTTP API, Cognito JWT authorizer, health Lambda（VPC 外・`GET /health` 認証なし）, attendance Lambda（VPC 内・JWT 必須の打刻/履歴/サマリ）, leave Lambda（VPC 内・JWT 必須の休暇申請/承認/却下）, users Lambda（VPC 内・JWT 必須の一覧/招待/更新・Cognito Admin IAM）, exports Lambda（VPC 内・JWT 必須の勤怠 CSV エクスポート・S3 Put/Presign IAM）, CORS（Amplify オリジン + ローカル `http://localhost:3000`） |
| amplify | Amplify Hosting アプリ + branch（ルート `frontend`、Next.js）。環境変数（Cognito / API URL）。GitHub 連携トークンは sensitive 変数 |
| monitoring | CloudWatch ダッシュボード骨格、SNS（アラーム本体は Phase 後半 / W-270） |
| github_oidc | OIDC provider, deploy roles（infra / backend。frontend は Amplify 連携時に追加） |

## State 管理

- **現状:** `envs/dev/providers.tf` でローカル state（S3 backend ブロックはコメントアウト）
- **推奨（初回 apply 前または直後）:** S3 + DynamoDB ロックへリモート化。key 例: `attendance/dev/terraform.tfstate`
- Cloud Agent などエフェメラル環境での apply は state 喪失リスクがある（[aws-auth-bootstrap.md](aws-auth-bootstrap.md)）
- 認証・OIDC 切り替え手順: [aws-auth-bootstrap.md](aws-auth-bootstrap.md)

## 主要変数

| 変数 | 例 | 説明 |
|------|-----|------|
| project_name | `attendance` | リソース名プレフィックス |
| environment | `dev` | 環境名 |
| aws_region | `ap-northeast-1` | |
| db_instance_class | `db.t4g.micro` | |
| cors_allow_localhost | `true`（dev） | `http://localhost:3000` を CORS に含めるか |
| cors_amplify_origin | Amplify の default branch URL | CORS 用（例: `https://main.<appId>.amplifyapp.com`）。`amplify` と `api` の循環回避のため初回は空、apply 後に `amplify_default_branch_url` 出力を設定 |
| amplify_github_access_token | （sensitive・任意） | Amplify の GitHub 連携。空でも `validate` 可。apply 前に設定 |
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
3. `api`（health / attendance / leave / users / exports を zip）
4. `monitoring` / `github_oidc`
5. `amplify`（Hosting）。API CORS の localhost は `cors_allow_localhost`。Amplify オリジンは apply 後に `cors_amplify_origin` へ反映（`api`↔`amplify` 循環回避）

## コスト抑制メモ

- NAT Gateway は 1 つ（AZ 冗長なし）
- RDS Multi-AZ オフ、バックアップ保持は Free Tier 向けに 1 日（有料枠なら延長可）
- 学習終了時は `terraform destroy` を前提にタグ `Project=attendance` を付与
