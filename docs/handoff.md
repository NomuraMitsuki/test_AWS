# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-17（W-280 PR #22 マージ済み。次は Mac で apply / invoke）

## 一言で

AWS 学習用の勤怠管理アプリ。W-001〜270・W-109・**W-280 のコードは `main`。** 本体 Terraform は以前 Mac で apply 済み。次は migrate Lambda 追加の再 apply → backend デプロイ（psycopg）→ invoke → 初回 admin。エージェントは apply / invoke をしない。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`（**private**）
- 作業ブランチ: **`main`**
- 直近マージ: PR #22（W-280 migrate Lambda / 初回 admin）

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, W-200〜W-270 完了。W-109 はコード完了＋本体 apply 済み。W-280 はコード完了（apply / invoke 待ち）
- Terraform Phase 1〜7 + Phase 9 monitoring + Phase 10 remote state
- backend: `health` + `attendance` + `leave` + `users` + `exports` + **`migrate`**（pytest）。`migrations/001`〜`003` は RDS 未適用
- frontend: Next.js 14（S01〜S12）+ Amplify Auth + API クライアント
- **CI/CD（W-260 + W-109）**:
  - plan/apply は Secret ありのとき OIDC + remote backend
  - apply は `environment: dev`。Required reviewers は private + Free のため**未設定**（`main` の infra push で apply が自動）
  - 正本: [docs/cicd/github-actions.md](cicd/github-actions.md)
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`（本体専用。bootstrap 非対象）
- bootstrap（tfstate S3 / DynamoDB）と本体スタックは **Mac で apply 済み**。bootstrap は destroy しない

## 次にやること（優先順）

1. **ユーザーの Mac（W-280 運用側）**: CI の OIDC は `AssumeRoleWithWebIdentity` で失敗している（PR plan も main の Backend deploy も）。関数作成は `./infra/scripts/tf-dev.sh apply`。続けて §E-0b で `psycopg` 入り zip を `update-function-code` してから `./infra/scripts/invoke-migrate.sh` → Cognito admin → seed。手順は [aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md) §E
2. GitHub Secrets は **Repository secrets** に入っている（OIDC 失敗は未登録ではなく ARN / 信頼ポリシーの切り分け）。Environment `dev` の secrets は空でよい
3. そのあと: 実ログイン（`frontend/.env.local` + `npm run dev`）。Amplify 利用時は `cors_amplify_origin`

## フロント画面レビュー（デモモード）

Cognito / API なしで UI 確認するときは `cd frontend && npm run dev:demo`（詳細は `frontend/README.md`）。本番 Amplify では `NEXT_PUBLIC_DEMO_MODE` を設定しない。実 Cognito は `.env.example` → `.env.local` して `npm run dev`。

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
- **apply / `gh secret set` / Lambda invoke はユーザーの Mac**（Cloud Agent 禁止）

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
W-280 のコードは実装済み。次はユーザー Mac での apply / backend デプロイ待ち / invoke / 初回 admin。
エージェントは terraform apply と Lambda invoke をしない。
```
