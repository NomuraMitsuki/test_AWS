# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-06（AWS 認証ブートストラップ手順を追加）

## 一言で

AWS 学習用の勤怠管理アプリ。設計資料と Phase 1 Terraform 骨格まで `main` に入った（本作業は認証手順 PR）。次は **永続 state 付き環境で一時 AWS 資格情報を渡し、W-108 の plan/apply** → OIDC を GitHub Secrets に登録。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: マージ後は **`main`**（認証手順は `docs/infra/aws-auth-bootstrap.md`）
- 直近マージ: PR #1〜#4

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当: skill + readonly subagent
- 日本語ルール / PR 作成時レビュールール
- WBS: W-001〜020, W-100〜107 完了。W-108 進行中
- Terraform Phase 1 コード: `infra/`（validate 済み、apply 未実施）
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **認証チェック**: `./infra/scripts/check-aws-auth.sh`

## 次にやること（優先順）

1. **ユーザーが AWS 資格情報を用意**（環境変数 or SSO）→ `./infra/scripts/check-aws-auth.sh` が OK
2. **state 保全**: ローカル PC 等で applyする、または先に S3 backend を有効化（Cloud Agent 単体 apply は非推奨）
3. **W-108 完了**: `infra/envs/dev` で `terraform plan` / `apply`
4. apply 後: `gha_infra_role_arn` / `gha_backend_role_arn` を GitHub Secrets に登録
5. **W-200**: HTTP API + JWT + health Lambda（Phase 2）

## 技術前提（変更しない）

- Next.js 14 / Amplify、API Gateway HTTP API、ドメイン別 Python Lambda
- Cognito（管理者招待のみ）、RDS PostgreSQL（プライベート）、S3 exports
- 単一 `dev`、`ap-northeast-1`
- 詳細: `docs/requirements.md`, `docs/superpowers/specs/2026-08-05-attendance-aws-design.md`

## 運用ルール（エージェント向け）

- ユーザー向け文書・PR 本文は日本語
- `docs/**` 等を含む **PR 新規作成直前**に `review-design-docs` → `design-doc-reviewer`
- 進捗は `docs/wbs.md` を更新
- Cloud では `/summarize` が効かないことがある → キリで本ファイルと WBS を更新

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
AWS 資格情報を環境変数（または AWS_PROFILE）で渡し、永続 state 環境で W-108 の terraform plan/apply を完了してください。
認証確認: ./infra/scripts/check-aws-auth.sh
手順: docs/infra/aws-auth-bootstrap.md
```
