# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-06（PR #4 マージ直後）

## 一言で

AWS 学習用の勤怠管理アプリ。設計資料と Phase 1 Terraform 骨格まで `main` に入った。次は AWS 認証付き plan/apply（W-108）または Phase 2 API（W-200）。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: **`main`（クリーン、origin と同期済み）**
- 直近マージ: PR #1〜#4

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当: skill + readonly subagent（`.cursor/skills/review-design-docs/`, `.cursor/agents/design-doc-reviewer.md`）
- 日本語ルール: `.cursor/rules/japanese-language.mdc`
- **PR 新規作成直前**に設計レビュー必須: `.cursor/rules/pr-design-review.mdc`（ファイル変更の都度ではない）
- WBS: `docs/wbs.md`（W-001〜020, W-100〜107 完了）
- Terraform Phase 1 コード: `infra/`（network / cognito / data / storage / monitoring / github_oidc）
- `terraform validate` 成功済み。**apply は未実施**（AWS 認証が必要）

## 次にやること（優先順）

1. **W-108**: AWS 資格情報（または GitHub OIDC）を用意し、`infra/envs/dev` で `terraform plan` / `apply`
2. **W-200**: HTTP API + JWT + health Lambda（Phase 2）
3. 以降は `docs/wbs.md` の W-210〜 に従う

## 技術前提（変更しない）

- Next.js 14 / Amplify、API Gateway HTTP API、ドメイン別 Python Lambda
- Cognito（管理者招待のみ）、RDS PostgreSQL（プライベート）、S3 exports
- 単一 `dev`、`ap-northeast-1`
- 詳細: `docs/requirements.md`, `docs/superpowers/specs/2026-08-05-attendance-aws-design.md`

## 運用ルール（エージェント向け）

- ユーザー向け文書・PR 本文は日本語（`.cursor/rules/japanese-language.mdc`）
- `docs/**` 等を含む **PR を新規作成する直前**に `review-design-docs` → `design-doc-reviewer` を実行
- 進捗は `docs/wbs.md` を更新
- Cloud では `/summarize` が効かないことがある → キリで本ファイルと WBS を更新し、新スレッドへ

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
ブランチは main。次は W-108（terraform plan/apply）からお願いします。
AWS 認証が無い場合は、認証手順の準備か W-200 のどちらを先にするか確認してください。
```
