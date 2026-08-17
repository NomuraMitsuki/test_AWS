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
- bootstrap ディレクトリ自体の CI validate ジョブ（ローカル `validate` で足りる。`fmt -recursive` は `infra/` 全体を拾う）

## 3. 方針（採用案 A）

独立した `infra/bootstrap` で state 用バケットとロックテーブルだけを作る（このディレクトリの state はローカル可。**destroy しない**）。その後 `infra/envs/dev` の `backend "s3"` を有効化し、本体スタックをリモート state で管理する。

## 4. 作業順序（Mac）

認証は `aws login` + `export-credentials`。`./infra/scripts/tf-dev.sh` は **本体（`infra/envs/dev`）専用**。bootstrap には使わない。

1. `cd infra/bootstrap` → `terraform init` → `terraform apply`（S3 + DynamoDB。この state はローカルでよい。**destroy しない**）
2. 出力の bucket / table 名を `infra/envs/dev/backend.hcl` に書き **コミットする**（gitignore しない。CI が読む）
3. `cd infra/envs/dev` → `terraform init -backend-config=backend.hcl`
4. `./infra/scripts/tf-dev.sh apply`（本体。RDS / Cognito / API / monitoring / OIDC 等）
5. `terraform output gha_infra_role_arn` / `gha_backend_role_arn` を控える
6. GitHub Secrets: `AWS_ROLE_ARN_INFRA` / `AWS_ROLE_ARN_BACKEND`。リージョンは workflow 既定 `ap-northeast-1`（Secret 不要）
7. Repository Environment `dev` に **reviewers を必須**（学習用 1 人可）。`main` push の apply が NAT / RDS を自動作成しないため
8. Amplify を接続した場合: `amplify_default_branch_url` を `cors_amplify_origin` に入れて再 apply（循環回避は現状どおり）

## 5. コード

### 5.1 `infra/bootstrap`

- S3: versioning、SSE、Block Public Access。bucket 名はグローバル衝突回避のため **アカウント ID を含める**（例: `attendance-tfstate-dev-<account_id>`）
- DynamoDB: lock 用テーブル（例: `attendance-tfstate-lock-dev`）
- 出力: bucket 名、table 名 → `infra/envs/dev/backend.hcl` へ転記してコミット

### 5.2 `infra/envs/dev` の backend

Terraform の `backend "s3"` は変数展開できない。

- `providers.tf`: `backend "s3" {}` を **部分設定**で有効化（key / region はここに書いてよい）
- `backend.hcl`: `bucket` と `dynamodb_table` のみ（bootstrap 出力）。**リポジトリにコミット**（gitignore しない）
- 初回は `backend.hcl.example` を置き、apply 後に実名を `backend.hcl` へ。CI は `terraform init -backend-config=backend.hcl`
- W-108 destroy 済みのため **本体 state の migrate は不要**（新規 apply）。`aws-auth-bootstrap.md` の「コメント解除＋先に bucket 手作り＋migrate」は本手順に置き換える。Cloud Agent apply は禁止のまま

### 5.3 `infra.yml`

| ジョブ | init / 未整備時 |
|--------|-----------------|
| validate | `-backend=false` のまま。必須ゲート |
| PR plan | **gate ジョブ**: `AWS_ROLE_ARN_INFRA` が空なら plan をスキップ＋注記（validate は必須）。Secret ありなら OIDC → `terraform init -backend-config=backend.hcl` → plan。init/plan 失敗はジョブ失敗（continue-on-error で握りつぶさない） |
| main apply | 現状どおり Secret 空ならスキップ。Secret ありなら `environment: dev`（reviewers 必須）→ OIDC → 同上 init → plan → apply。`-backend=false` は使わない |

`backend.hcl` 未コミットや bucket 未作成の状態で Secret だけあると plan は赤になる。順序は §4 どおり bootstrap → `backend.hcl` コミット → 本体 apply → Secrets。

## 6. 検証

- `infra/bootstrap` と `infra/envs/dev`: `terraform fmt` / `init -backend=false` / `validate`（bootstrap の validate はローカル。CI validate ジョブは従来どおり `envs/dev`）
- docs 更新対象（実装時）:
  - [aws-auth-bootstrap.md](../../infra/aws-auth-bootstrap.md): 前提の local state / Cloud Agent apply 許容を改める。§C は Mac + `tf-dev.sh`（本体）。§D を本スペック §4 に置き換え（手作り bucket + migrate は捨てる）
  - [github-actions.md](../../cicd/github-actions.md): 現状＝validate 必須、plan/apply は OIDC + remote backend。apply は `environment: dev` **reviewers 必須**
  - [terraform-design.md](../../infra/terraform-design.md): `infra/bootstrap` を構成に追加。State は S3。学習終了時の destroy は **本体のみ**（bootstrap は残すか明示的に最後）
  - handoff / WBS（コード完了とユーザー apply 待ちを区別）
- apply / Secrets 実登録はユーザー作業（手順に `gh secret set` 例を書いてよい。エージェントは実行しない）
- 実装計画はスペック承認後に `docs/superpowers/plans/` へ書く

## 7. 完了後

- WBS W-109 を、コード完了と「ユーザー apply / Secrets 待ち」が区別できるメモにする（親がステータス確定）
- 次: ユーザーが Mac で apply したあと、実 Cognito ログインや CI plan の確認
