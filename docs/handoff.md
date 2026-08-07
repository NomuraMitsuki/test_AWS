# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-07（W-108 完了・リソースは destroy 済み）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform はローカル apply 成功まで確認済み（その後 destroy）。次は **W-109（再 apply 後の GitHub Secrets / OIDC）** または **W-200（Phase 2 API）**。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: マージ後は **`main`**（PR #6）
- 直近: PR #1〜#4 マージ済み。PR #6 に認証手順 + `tf-dev.sh`

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- WBS: W-001〜020, W-100〜108 完了
- Terraform Phase 1: コード + ローカル plan/apply 検証（Free Tier 向け RDS backup=1 日）
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`（`auth` / `plan` / `apply`）
- AWS リソースは確認後 **destroy 済み**（デフォルト VPC は残る）

## 次にやること（優先順）

1. **W-109**: 必要になったタイミングで再 `apply` → `gha_*_role_arn` を GitHub Secrets に登録 → CI の OIDC plan を有効化（リモート state も検討）
2. **W-200**: HTTP API + JWT + health Lambda（Phase 2）
3. 以降は `docs/wbs.md` の W-210〜

## 技術前提（変更しない）

- Next.js 14 / Amplify、API Gateway HTTP API、ドメイン別 Python Lambda
- Cognito（管理者招待のみ）、RDS PostgreSQL（プライベート）、S3 exports
- 単一 `dev`、`ap-northeast-1`

## 運用ルール（エージェント向け）

- ユーザー向け文書・PR 本文は日本語
- `docs/**` 等を含む **PR 新規作成直前**に設計資料レビュー
- 進捗は `docs/wbs.md` を更新

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
W-108 完了・AWS リソースは destroy 済み。次は W-109（Secrets/OIDC）または W-200。
```
