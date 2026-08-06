# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-06（tf-dev.sh: aws login + plan/apply 一括）

## 一言で

AWS 学習用の勤怠管理アプリ。設計資料と Phase 1 Terraform 骨格まであり、ローカルでは `./infra/scripts/tf-dev.sh` で plan/apply 可能。次は W-108 の apply 完了と OIDC Secrets 登録、その後 W-200。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: マージ後は **`main`**
- 直近マージ: PR #1〜#4

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当: skill + readonly subagent
- 日本語ルール / PR 作成時レビュールール
- WBS: W-001〜020, W-100〜107 完了。W-108 進行中
- Terraform Phase 1 コード: `infra/`（validate 済み）
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`（`auth` / `plan` / `apply`）
- **CLI 疎通**: `./infra/scripts/check-aws-auth.sh`

## 次にやること（優先順）

1. ローカル PC で `aws login`（または SSO）→ `./infra/scripts/tf-dev.sh plan` / `apply`
2. **state 保全**: ローカル PC 等で apply（Cloud Agent 単体 apply は非推奨）。必要なら S3 backend
3. **W-108 完了**: plan/apply 成功、fmt/validate も確認
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
ローカルでは ./infra/scripts/tf-dev.sh plan|apply（aws login + export-credentials 込み）を使います。
手順: docs/infra/aws-auth-bootstrap.md
次は W-108 完了（apply + Secrets）または W-200 です。
```
