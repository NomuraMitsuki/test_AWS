# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-07（W-250 フロント + Amplify 実装後。次は W-260 / W-109 方針）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform、W-200〜W-240（API）、**W-250（Next.js フロント + Amplify モジュール + API CORS）** までコード実装済み（apply なし）。**次は W-260（CI 完成）またはユーザー方針に従い W-109（再 apply / Secrets）**。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: **`cursor/w250-frontend-a099`**（マージ後は `main`）
- 直近マージ: PR #1〜#13（W-250 は PR #14 予定）

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, W-200〜W-240、**W-250 実装完了（apply なし・WBS ステータスは親が更新）**
- Terraform Phase 1〜7（api CORS / amplify モジュール含む）コード
- backend: `health` + `attendance` + `leave` + `users` + `exports`（pytest）+ `migrations/001`〜`003`
- frontend: Next.js 14（S01〜S12）+ Amplify Auth + API クライアント。CI は `.github/workflows/frontend.yml`（lint/build のみ）
- Amplify: Terraform モジュールで Hosting（auto build 可）。**Actions からのデプロイジョブ完成は W-260**（Hosting の auto build 自体は W-250）
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`
- AWS リソースは確認後 **destroy 済み**（再 apply は未実施）

## 次にやること（優先順）

1. **W-260**: GitHub Actions（backend / frontend）完成。Amplify デプロイ連携など
2. **W-109**: **API（W-210〜）およびフロント（W-250）完了後**に再 apply → GitHub Secrets / OIDC CI（それまで着手しない）。Amplify apply 時は `amplify_github_access_token` と `cors_amplify_origin` の設定に注意

## 技術前提（変更しない）

- Next.js 14 / Amplify、API Gateway HTTP API、ドメイン別 Python Lambda
- Cognito（管理者招待のみ）、RDS PostgreSQL（プライベート）、S3 exports
- 単一 `dev`、`ap-northeast-1`
- health は VPC 外、attendance 以降のドメイン Lambda は VPC 内

## 運用ルール（エージェント向け）

- ユーザー向け文書・PR 本文は日本語
- 複数ステップの実装は親が抱え込まず `implement-with-subagent` → `implementation-worker`
- 実装完了後の **WBS ステータス更新と PR 操作は親**が行う
- `docs/**` 等を含む **PR 新規作成直前**に設計資料レビュー
- 進捗は `docs/wbs.md` を更新
- **W-109 を API／フロント完了前に進めない**

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
次は W-260（CI）またはユーザー方針で W-109。W-250 は実装済み。
```
