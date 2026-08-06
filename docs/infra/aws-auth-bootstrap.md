# AWS 認証ブートストラップ（W-108）

W-108（fmt / validate / plan）を資格情報付きで完了し、OIDC 利用に進むための初回 `apply` までを含む手順。

## 前提

- AWS アカウント（学習用サンドボックス可）と、リソース作成権限を持つ IAM プリンシパル
- リージョン: `ap-northeast-1`
- リポジトリ: `NomuraMitsuki/test_AWS`
- Terraform `>= 1.5`（CI / 推奨ローカル: `1.9.8`）と AWS CLI v2

**鶏卵問題:** GitHub Actions の OIDC ロール（`attendance-dev-gha-infra` 等）は Terraform apply 後に初めて存在する。したがって **初回 apply はローカル（または Cloud Agent）の一時資格情報** で行い、成功後にロール ARN を GitHub Secrets へ登録する。

**State（重要）:** 現状 `infra/envs/dev/providers.tf` は **ローカル state**（S3 backend はコメントアウト）。Cloud Agent のエフェメラル環境で apply すると、環境破棄と共に state を失い、以降の plan/apply や GHA と整合できなくなる。初回 apply は **state を保持できるマシン**（ローカル PC、永続ディスク付きランナー等）で行うか、apply 前に [terraform-design.md](terraform-design.md) の State 管理に従い S3 + DynamoDB へリモート化する。OIDC 切り替え（§D）は、その state が以降も参照できることが前提。**GitHub Actions と state を共有するならリモート state が必須**（現状の `infra.yml` は `terraform init -backend=false` のためローカル state を読めない）。

## A. 初回 apply 用の資格情報

次のいずれかでよい（長期キーをリポジトリに置かない）。

### A-1. 環境変数（Cloud Agent / CI 外の一時利用向け）

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...          # 一時クレデンシャルの場合
export AWS_DEFAULT_REGION=ap-northeast-1
aws sts get-caller-identity          # Account / Arn が表示されれば OK
```

Cloud Agent に渡す場合は、チャットや Environment Secrets 経由で上記を設定する。値をコミットしない。

### A-2. AWS SSO（ローカル推奨）

```bash
aws configure sso
# SSO start URL / リージョン / アカウント / ロールを対話設定
aws sso login --profile attendance-dev
export AWS_PROFILE=attendance-dev
export AWS_DEFAULT_REGION=ap-northeast-1
aws sts get-caller-identity
```

### A-3. 名前付きプロファイル（アクセスキー）

```bash
aws configure --profile attendance-dev
export AWS_PROFILE=attendance-dev
aws sts get-caller-identity
```

## B. 認証確認スクリプト

```bash
./infra/scripts/check-aws-auth.sh
```

成功時のみ `terraform plan` に進む。

## C. 初回 plan / apply（W-108）

W-108 の完了条件: `terraform fmt` / `validate` / **資格情報付き `plan`**。OIDC を有効にするには続けて **初回 `apply`** が必要（これも W-108 の残作業として扱う）。

```bash
cd infra/envs/dev
cp -n terraform.tfvars.example terraform.tfvars   # 初回のみ
# リモート state にする場合は providers.tf の backend "s3" を有効化し、先に bucket/lock を用意してから:
terraform init
terraform fmt -check -recursive ../..
terraform validate
terraform plan -out=tfplan
# 差分を確認（RDS が publicly_accessible でないこと、S3 がパブリックでないこと）
terraform apply tfplan
```

apply 後、次を控える（state と一緒に保管する）:

```bash
terraform output gha_infra_role_arn
terraform output gha_backend_role_arn
```

## D. GitHub OIDC への切り替え

前提: §C の state が以降の実行環境から参照できること。**CI の OIDC plan を実リソースに対して正しく回すには、S3 backend 有効化後に `infra.yml` の `-backend=false` を外す**（Secrets 登録だけでは不足）。

1. （推奨）`providers.tf` の `backend "s3"` を有効化し、state 用 bucket / DynamoDB を用意して `terraform init -migrate-state`
2. リポジトリ Settings → Secrets and variables → Actions に登録:
   - `AWS_ROLE_ARN_INFRA` = `gha_infra_role_arn` の値
   - `AWS_ROLE_ARN_BACKEND` = `gha_backend_role_arn` の値
3. Repository Environment `dev`: 現状の `infra.yml` は plan までのため任意。apply ジョブを追加するときは reviewers 付きで必須（[github-actions.md](../cicd/github-actions.md)）
4. `infra.yml` でリモート state を使うよう `terraform init`（`-backend=false` なし）に更新する
5. 以降の PR では OIDC で `plan` する

詳細は [docs/cicd/github-actions.md](../cicd/github-actions.md)。

## E. 権限の目安（初回ローカル用）

学習用なら AdministratorAccess 相当でもよい。絞る場合の目安:

- EC2 / VPC / RDS / S3 / Cognito / Secrets Manager / SNS / CloudWatch / IAM（OIDC provider・ロール作成）

最小権限への絞り込みは apply 安定後の後続課題。

## F. トラブルシュート

| 症状 | 確認 |
|------|------|
| `Unable to locate credentials` | `AWS_PROFILE` / 環境変数 / `aws sts get-caller-identity` |
| `ExpiredToken` | SSO 再ログイン、またはセッション更新 |
| OIDC plan がスキップ／失敗 | Secrets にロール ARN があるか、初回 apply 済みか |
| `AccessDenied` on IAM OIDC | 初回プリンシパルに `iam:CreateOpenIDConnectProvider` 等があるか |
