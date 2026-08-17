# Phase 11 — RDS マイグレーションと初回 admin（W-280）

**日付**: 2026-08-17  
**ステータス**: Approved（エージェントは apply / Lambda invoke しない）  
**WBS**: W-280  
**親スペック**: [2026-08-05-attendance-aws-design.md](2026-08-05-attendance-aws-design.md) §4.4.1 / §4.5  
**手順正本（運用）**: [docs/infra/aws-auth-bootstrap.md](../../infra/aws-auth-bootstrap.md) §E

## 1. ゴール

プライベート RDS に `backend/migrations/001`〜`003` を適用し、最初の `admin` を Cognito + `users` 行として作れるようにする。Mac から踏み台 EC2 なしで実行できる。

完了条件（リポジトリ側）: migrate Lambda + 手動 invoke 手順 + 初回 admin 手順が揃い、pytest / terraform validate が通る。  
完了条件（運用側・ユーザー）: Mac で本体を再 apply し、`psycopg` 入り zip を載せてから migrate を invoke し、admin でログインできる。zip は `backend.yml` の UpdateFunctionCode、または OIDC 失敗時は `package-migrate.sh`。

## 2. 非ゴール

- エージェントからの `terraform apply` / Lambda invoke
- RDS のパブリック化、常時起動の bastion EC2
- マイグレーションの自動適用（CI の main apply に載せない。課金・破壊操作を人が起動する）
- Terraform による admin 完全自動シード（親スペックどおり手動）
- migrate を HTTP API に公開すること（JWT 無しの破壊操作になる）

## 3. 方針（採用案 A）

ドメイン Lambda と同じ VPC / SG に **migrate Lambda** を置き、Secrets Manager の DB 認証情報で `psql` 相当（Python `psycopg`）を実行する。起動は Mac から `aws lambda invoke`（既存の `aws login` + `export-credentials`）。

採用しない案:

- **bastion EC2 + SSM ポートフォワード**: 学習には正しいが、インスタンス課金と SG 追加が乗る。NAT は既にあるので Lambda の方が既存構成に乗る
- **RDS を一時 public**: 設計（プライベートのみ）に反する

## 4. 作業順序（Mac・実装後）

認証は本体と同じ（`eval "$(aws configure export-credentials --format env)"` または専用スクリプト）。

1. 本機能のコードを `main` に載せたあと `./infra/scripts/tf-dev.sh apply`（migrate Lambda 追加。NAT / RDS は既存）。Terraform の zip はソース + SQL のみで `psycopg` は入らない
2. `psycopg` を同梱する。`backend.yml` の UpdateFunctionCode が使えればそれでよい。OIDC が `AssumeRoleWithWebIdentity` で失敗している間は `./infra/scripts/package-migrate.sh`（Mac の素の `pip install -t` は使わない）
3. migrate を invoke し `001`〜`003` を適用（`CREATE IF NOT EXISTS` で再実行可）
4. Cognito `AdminCreateUser` + グループ `admin`（username は email）
5. 同じメール / `cognito_sub` / `role=admin` / `status=active` を `users` に入れる（invoke の seed ペイロード）
6. フロントは `frontend/.env.example` を `.env.local` にして `npm run dev`。Amplify を使う場合は `amplify_default_branch_url` を `cors_amplify_origin` に入れて再 apply

## 5. コード

### 5.1 `backend/migrate`

- zip に `backend/migrations/*.sql` を同梱（ファイル名順）
- 環境変数 `DB_SECRET_ARN`（既存ドメイン Lambda と同じ）
- デフォルト: マイグレーション実行
- 任意イベント: 初回 admin の `users` INSERT（email / cognito_sub / name）。メールまたは `cognito_sub` の重複は成功扱いで既存行を返すか、明確なエラーメッセージで失敗する（HTTP ステータスは使わない。invoke の payload で結果を返す）
- API Gateway には繋がない

### 5.2 Terraform

- `infra/modules/api`（または同等）に `attendance-dev-migrate`。VPC 内、DB secret 読取、タイムアウトは DDL 用に余裕を見る
- HTTP ルートは作らない
- `backend.yml` の main デプロイ対象に関数名を足す（コード更新用）
- 実装時に次も更新する: [terraform-design.md](../../infra/terraform-design.md) の Lambda 一覧とデプロイ順、[monitoring.md](../../ops/monitoring.md) および monitoring モジュール（既存は Lambda×5。migrate をダッシュボードに含めるかは最小で Errors アラームのみ可）、親スペック §4.3 の関数一覧

### 5.3 手順書

- [aws-auth-bootstrap.md](../../infra/aws-auth-bootstrap.md) §E は本 PR で Phase 11 参照済み。実装時は §4 の Mac コマンド（invoke / Cognito CLI）を §E に具体化する
- Cognito CLI 例（`terraform output cognito_user_pool_id`、`admin-create-user`、`admin-add-user-to-group`、`admin-get-user` で `sub`）
- `tf-dev.sh` は本体専用のまま。migrate invoke は別の短いスクリプトか、手順書の `aws lambda invoke` でよい

## 6. 検証

- pytest（DB はモックまたはテスト用接続。Cognito は呼ばない）
- `terraform fmt` / `init -backend=false` / `validate`
- apply / invoke はユーザー

## 7. 完了後

- WBS W-280 をコード完了とユーザー apply / invoke 待ちで区別する（親）
- 次: 実ログイン確認。Amplify CORS は URL が取れてから
