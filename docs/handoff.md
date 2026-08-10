# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-10（W-270 を main にマージ。次は W-109）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform、W-200〜W-260（API / フロント / CI/CD）、**W-270（CloudWatch ダッシュボード・アラーム仕上げ）** までコード実装済み（apply / Secrets 実登録なし）。フロントはデモモード（`npm run dev:demo`）あり。**次は W-109（再 apply / Secrets）**。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: **`main`**
- 直近マージ: PR #1〜#18（W-270 #18）

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, W-200〜W-270 完了（apply / Secrets なし）。**次の未着手は W-109**
- Terraform Phase 1〜7（api CORS / amplify モジュール含む）+ Phase 9 monitoring 仕上げコード
- backend: `health` + `attendance` + `leave` + `users` + `exports`（pytest）+ `migrations/001`〜`003`
- frontend: Next.js 14（S01〜S12）+ Amplify Auth + API クライアント
- **CI/CD（W-260）**:
  - `.github/workflows/backend.yml` — pytest / compileall 必須、main で任意 Lambda deploy
  - `.github/workflows/frontend.yml` — lint/build 必須、main で任意 Amplify `start-job`（`AWS_ROLE_ARN_INFRA` + `AMPLIFY_APP_ID`）
  - `.github/workflows/infra.yml` — fmt + validate 必須、main で plan→apply 骨格（`environment: dev`）
  - 正本: [docs/cicd/github-actions.md](cicd/github-actions.md)
- **監視（W-270）**: `infra/modules/monitoring` にダッシュボード＋主要アラーム。正本 [docs/ops/monitoring.md](ops/monitoring.md)。apply は未実施
- Amplify: Terraform モジュールで Hosting（auto build 可）。Actions の `start-job` は補助
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`
- AWS リソースは確認後 **destroy 済み**（再 apply は未実施）

## 次にやること（優先順）

1. **W-109**: 再 apply → GitHub Secrets / OIDC CI。Amplify apply 時は `amplify_github_access_token` と `cors_amplify_origin` の設定に注意。リモート state 整備前は CI apply しない。監視リソースもこの apply で作成される

## フロント画面レビュー（デモモード）

Cognito / API なしで UI 確認するときは `cd frontend && npm run dev:demo`（詳細は `frontend/README.md`）。本番 Amplify では `NEXT_PUBLIC_DEMO_MODE` を設定しない。

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
- **W-109 を API／フロント完了前に進めない**（API／フロントは完了済み）

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
次は W-109（再 apply / Secrets）。W-270 監視仕上げはコード実装済み（apply なし）。
```
