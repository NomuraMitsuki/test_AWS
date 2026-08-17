# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-17（W-281: `tf-dev.sh up` / `down`。エージェントは apply / destroy / invoke しない）

## 一言で

AWS 学習用の勤怠管理アプリ。W-001〜270・W-109・W-280 のコードは `main`。本体の立ち上げ / 停止は **`./infra/scripts/tf-dev.sh up` / `down`**（W-281）。bootstrap（tfstate 用 S3 / DynamoDB）は消さない。エージェントは apply / destroy / Lambda invoke / `gh secret set` をしない。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`（公開準備中。アカウント ID / 個人メールはコミットしない）
- 作業ブランチ: **`main`**（W-281 は PR 待ちのとき `cursor/tf-dev-up-down-a099`）
- 直近の本体運用: Mac で apply → Linux zip → invoke → Cognito admin → ローカル `npm run dev` まで確認済み。Amplify の GitHub 公開はしない

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, W-200〜W-270 完了。W-109 はコード完了＋本体 apply 済み。W-280 はコード完了（運用側の migrate / admin も Mac で実施済み）
- Terraform Phase 1〜7 + Phase 9 monitoring + Phase 10 remote state
- backend: `health` + `attendance` + `leave` + `users` + `exports` + **`migrate`**（pytest）
- frontend: Next.js 14（S01〜S12）+ Amplify Auth + API クライアント
- **CI/CD（W-260 + W-109）**:
  - plan/apply は Secret ありのとき OIDC + remote backend
  - apply は `environment: dev`。Required reviewers は private + Free のため**未設定**（`main` の infra push で apply が自動）
  - CI の OIDC は `AssumeRoleWithWebIdentity` で失敗することがある。失敗時は Mac の `tf-dev.sh` が正
  - 正本: [docs/cicd/github-actions.md](cicd/github-actions.md)
- **認証・立ち上げ手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`（本体専用。bootstrap 非対象）
- bootstrap は **Mac で apply 済み**。**destroy しない**
- 公開用に `infra/envs/dev/backend.hcl` はプレースホルダ（`REPLACE_AFTER_BOOTSTRAP`）。アカウント ID はコミットしない。Mac の init / apply / destroy ではローカルだけ実名に書き換える

## 次にやること（優先順）

1. **ユーザーの Mac**: 課金を止めたいときは本体だけ停止する。W-281 マージ後:

   ```bash
   git pull origin main
   ./infra/scripts/tf-dev.sh down
   ```

   再立ち上げ:

   ```bash
   ./infra/scripts/tf-dev.sh up --admin-email you@example.com
   cd frontend && npm run dev
   ```

   `up` / `down` とも `[y/N]`。bootstrap は触らない。`backend.hcl` はローカルで実名にしてコミットしない。手順正本: [aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
2. GitHub Secrets は **Repository secrets** に入っていると、プレースホルダの `backend.hcl` では CI plan が赤になる。plan / apply を止めるなら `AWS_ROLE_ARN_INFRA` を消す。Environment `dev` の secrets は空でよい
3. Amplify の GitHub 接続は必須ではない（公開しない方針）

## フロント画面レビュー（デモモード）

Cognito / API なしで UI 確認するときは `cd frontend && npm run dev:demo`（詳細は `frontend/README.md`）。本番 Amplify では `NEXT_PUBLIC_DEMO_MODE` を設定しない。実 Cognito は `up` が書く `.env.local` か、`.env.example` → `.env.local` して `npm run dev`。

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
- **apply / destroy / `gh secret set` / Lambda invoke はユーザーの Mac**（Cloud Agent 禁止）。`tf-dev.sh up` / `down` もエージェントは実行しない

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
本体の立ち上げ / 停止は ./infra/scripts/tf-dev.sh up / down（W-281）。
エージェントは terraform apply / destroy と Lambda invoke をしない。bootstrap は destroy しない。
```
