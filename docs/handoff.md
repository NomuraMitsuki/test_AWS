# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-17（W-109 コード実装。次はユーザー Mac で apply / Secrets）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform、W-200〜W-270 までコード実装済み。W-109 の **リポジトリ側**（`infra/bootstrap` / S3 backend / `infra.yml` / 手順書）は実装済み。**apply / Secrets 実登録は未実施。次はユーザーの Mac。**

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: **`cursor/w109-remote-state-a099`**（W-109 実装）
- 直近マージ: PR #1〜#18（W-270 #18）

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, W-200〜W-270 完了（apply / Secrets なし）。W-109 はコード完了・運用側（Mac apply / Secrets）待ち
- Terraform Phase 1〜7（api CORS / amplify モジュール含む）+ Phase 9 monitoring 仕上げコード
- **W-109 コード**: `infra/bootstrap`、`envs/dev` の S3 backend、`infra.yml` の remote init、手順書。validate 済み。apply なし
- backend: `health` + `attendance` + `leave` + `users` + `exports`（pytest）+ `migrations/001`〜`003`
- frontend: Next.js 14（S01〜S12）+ Amplify Auth + API クライアント
- **CI/CD（W-260 + W-109）**:
  - `.github/workflows/backend.yml` — pytest / compileall 必須、main で任意 Lambda deploy
  - `.github/workflows/frontend.yml` — lint/build 必須、main で任意 Amplify `start-job`（`AWS_ROLE_ARN_INFRA` + `AMPLIFY_APP_ID`）
  - `.github/workflows/infra.yml` — fmt + validate 必須。plan/apply は Secret ありのとき OIDC + `init -backend-config=backend.hcl`。apply は `environment: dev`（reviewers 必須）
  - 正本: [docs/cicd/github-actions.md](cicd/github-actions.md)
- **監視（W-270）**: `infra/modules/monitoring` にダッシュボード＋主要アラーム。正本 [docs/ops/monitoring.md](ops/monitoring.md)。apply は未実施
- Amplify: Terraform モジュールで Hosting（auto build 可）。Actions の `start-job` は補助
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`（本体専用。bootstrap 非対象）
- AWS リソースは確認後 **destroy 済み**（再 apply はユーザー Mac 待ち）

## 次にやること（優先順）

1. **ユーザーの Mac（W-109 運用側）**: `infra/bootstrap` apply → `backend.hcl` に実名を書いてコミット → `./infra/scripts/tf-dev.sh apply` → GitHub Secrets（`AWS_ROLE_ARN_INFRA` / `AWS_ROLE_ARN_BACKEND`）→ Environment `dev` の reviewers 必須。エージェントは apply / Secrets を実行しない
2. そのあと: 実 Cognito ログイン、migrations、CI plan の確認

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
- **apply / `gh secret set` はユーザーの Mac**（Cloud Agent 禁止）

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
W-109 のコードは実装済み。次はユーザー Mac での bootstrap / 本体 apply / Secrets。
エージェントは terraform apply と gh secret set をしない。
```
