# AWS 認証ブートストラップ（W-109）

リモート Terraform state（S3 + DynamoDB）を用意し、本体スタックを Mac で apply したあと、OIDC ロール ARN を GitHub Secrets に登録するまでの手順。

**エージェント（Cloud Agent）は `terraform apply` / `terraform destroy` / `gh secret set` を実行しない。** エフェメラル環境で state を失うため、apply と Secrets 登録は **ユーザーの Mac** で行う。

## 前提

- AWS アカウント（学習用サンドボックス可）と、リソース作成権限を持つ IAM プリンシパル
- リージョン: `ap-northeast-1`
- リポジトリ: `NomuraMitsuki/test_AWS`
- Terraform `>= 1.5`（CI / 推奨ローカル: `1.9.8`）と AWS CLI v2
- GitHub CLI（`gh`）は Secrets 登録時に使用（任意。コンソールでも可）

**鶏卵問題:** GitHub Actions の OIDC ロール（`attendance-dev-gha-infra` 等）は本体 Terraform apply 後に初めて存在する。したがって **初回の本体 apply は Mac の一時資格情報** で行い、成功後にロール ARN を GitHub Secrets へ登録する。

**State:** 本体（`infra/envs/dev`）は S3 backend。バケットとロックテーブルは独立した `infra/bootstrap` が作る（bootstrap の state はローカルでよい。**destroy しない**）。`./infra/scripts/tf-dev.sh` は **本体専用** で、bootstrap には使わない。

W-108 時点のリソースは destroy 済みのため、**本体 state の migrate は不要**（新規 apply）。バケットをコンソールで手作りしない。

## A. 初回 apply 用の資格情報

次のいずれかでよい（長期キーをリポジトリに置かない）。**Cloud Agent に資格情報を渡して apply しない。**

### A-1. 環境変数（Mac の一時利用）

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...          # 一時クレデンシャルの場合
export AWS_DEFAULT_REGION=ap-northeast-1
aws sts get-caller-identity          # Account / Arn が表示されれば OK
```

値をコミットしない。

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

### A-4. `aws login`（ブラウザログイン）

```bash
aws login
aws sts get-caller-identity
```

`aws login` の資格情報は AWS CLI では使えるが、Terraform の AWS provider が直接拾えないことがある。その場合は次を挟む（本体の [`tf-dev.sh`](../../infra/scripts/tf-dev.sh) が自動化する）:

```bash
eval "$(aws configure export-credentials --format env)"
```

## B. 一括スクリプト（本体専用）

`./infra/scripts/tf-dev.sh` は **`infra/envs/dev` 専用**。`infra/bootstrap` には使わない。

リポジトリルートから（`backend.hcl` に bootstrap 出力の実名を書いたあと）:

```bash
./infra/scripts/tf-dev.sh auth    # login（必要時）+ export-credentials + 確認
./infra/scripts/tf-dev.sh plan    # 上記のあと terraform init -backend-config=backend.hcl / plan -out=tfplan
./infra/scripts/tf-dev.sh apply   # 内部で plan し直し → [y/N] 確認 → apply
```

`apply` は単体で完結する（直前の `plan` サブコマンドは必須ではない。付けると plan が二重になる）。保存済み plan への `terraform apply tfplan` には Terraform 標準の yes/no が出ないため、スクリプト側で `[y/N]` を聞く。

AWS CLI の疎通確認だけなら:

```bash
./infra/scripts/check-aws-auth.sh
```

（CLI が通っても Terraform 用には `export-credentials` または `tf-dev.sh` が必要な場合がある。）

## C. bootstrap（Mac）

state 用 S3 と DynamoDB だけを作る。詳細は [`infra/bootstrap/README.md`](../../infra/bootstrap/README.md)。

```bash
cd infra/bootstrap
eval "$(aws configure export-credentials --format env)"  # aws login 利用時
terraform init
terraform apply
terraform output
```

**`terraform destroy` しない。** 出力の `bucket_name` / `dynamodb_table_name` を `infra/envs/dev/backend.hcl` に書いて **コミットする**（gitignore しない。CI が読む）:

```hcl
bucket         = "attendance-tfstate-dev-<account_id>"
dynamodb_table = "attendance-tfstate-lock-dev"
```

プレースホルダ `REPLACE_AFTER_BOOTSTRAP` のままだと、本体の `terraform init` は失敗してよい。

## D. 作業順序（Mac・正本）

認証は `aws login` + `export-credentials`。順序を守る（`backend.hcl` 未コミットやバケット未作成の状態で Secret だけあると CI plan は赤になる）。

1. `cd infra/bootstrap` → `terraform init` → `terraform apply`（S3 + DynamoDB。この state はローカルでよい。**destroy しない**）
2. 出力の bucket / table 名を `infra/envs/dev/backend.hcl` に書き **コミットする**
3. `cd infra/envs/dev` → `terraform init -backend-config=backend.hcl`
4. `./infra/scripts/tf-dev.sh apply`（本体。RDS / Cognito / API / monitoring / OIDC 等）
5. `terraform output gha_infra_role_arn` / `gha_backend_role_arn` を控える
6. GitHub Secrets を登録する（リージョンは workflow 既定 `ap-northeast-1`。Secret 不要）:

   ```bash
   cd infra/envs/dev
   gh secret set AWS_ROLE_ARN_INFRA --body "$(terraform output -raw gha_infra_role_arn)"
   gh secret set AWS_ROLE_ARN_BACKEND --body "$(terraform output -raw gha_backend_role_arn)"
   ```

   コンソールなら Settings → Secrets and variables → Actions に同名で貼る。
7. Repository Environment `dev` に **reviewers を必須**（学習用 1 人可）。`main` push の apply が NAT / RDS を自動作成しないため
8. Amplify を接続した場合: `amplify_default_branch_url` を `cors_amplify_origin` に入れて再 apply（循環回避は現状どおり）

CI の動きは [docs/cicd/github-actions.md](../cicd/github-actions.md)。validate は `init -backend=false` のまま必須。PR plan / main apply は Secret があるときだけ OIDC + `init -backend-config=backend.hcl`。

## E. apply 後の残作業（短く）

本体 apply が終わったら、アプリを動かすために次を行う（詳細は各設計資料）:

- **初回 admin:** Cognito コンソールまたは `AdminCreateUser` で管理者を招待し、仮パスワードでログインする
- **migrations:** RDS に `backend/migrations/001`〜`003` を適用する（プライベートサブネットのため、踏み台または一時的な接続手段が必要）
- Amplify の default branch URL が分かったら `cors_amplify_origin` を更新して再 apply（§D の 8）

## F. 権限の目安（初回ローカル用）

学習用なら AdministratorAccess 相当でもよい。絞る場合の目安:

- EC2 / VPC / RDS / S3 / Cognito / Secrets Manager / SNS / CloudWatch / IAM（OIDC provider・ロール作成）
- bootstrap: S3 バケット作成、DynamoDB テーブル作成

最小権限への絞り込みは apply 安定後の後続課題。

## G. トラブルシュート

| 症状 | 確認 |
|------|------|
| `Unable to locate credentials` | `AWS_PROFILE` / 環境変数 / `aws sts get-caller-identity` |
| CLI の sts は通るが Terraform だけ失敗 | `aws login` 利用時は `export-credentials` が必要。本体は `./infra/scripts/tf-dev.sh plan` を使う |
| `ExpiredToken` | `aws login` / SSO 再ログイン、またはセッション更新 |
| `backend.hcl` の bucket が見つからない | bootstrap apply 済みか、出力を `backend.hcl` に書いてコミットしたか |
| OIDC plan がスキップ | Secrets に `AWS_ROLE_ARN_INFRA` があるか（空なら skip-note。validate は必須） |
| OIDC plan / apply が赤 | Secret ありなのにバケット未作成、または `backend.hcl` がプレースホルダのまま。順序は §D |
| `AccessDenied` on IAM OIDC | 初回プリンシパルに `iam:CreateOpenIDConnectProvider` 等があるか |
