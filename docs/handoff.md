# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-07（W-200 HTTP API + health 実装）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform はローカル apply 成功まで確認済み（その後 destroy）。**W-200（HTTP API + JWT + health）のコードは `cursor/w200-http-api-health-a099` に実装済み**（apply なし・pytest / terraform validate）。次は PR マージ後の W-210 系、または必要なら W-109。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: W-200 実装は **`cursor/w200-http-api-health-a099`**（マージ後は `main`）
- 直近: PR #1〜#7 マージ済み。W-200 実装ブランチあり

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006 完了。W-109 未着手。W-200 は実装ブランチ上でコード完了（WBS ステータスは親が更新）
- Terraform Phase 1: コード + ローカル plan/apply 検証（Free Tier 向け RDS backup=1 日）
- **Phase 2（W-200）**: `backend/health` + `infra/modules/api` + `envs/dev` 配線（apply は未実施）
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`（`auth` / `plan` / `apply`）
- AWS リソースは確認後 **destroy 済み**（デフォルト VPC は残る）

## 次にやること（優先順）

1. **W-200**: 設計レビュー → PR 作成・マージ。WBS を完了にする（親）
2. **W-109**: 必要になったタイミングで再 `apply` → GitHub Secrets / OIDC CI
3. 以降は `docs/wbs.md` の W-210〜

## 技術前提（変更しない）

- Next.js 14 / Amplify、API Gateway HTTP API、ドメイン別 Python Lambda
- Cognito（管理者招待のみ）、RDS PostgreSQL（プライベート）、S3 exports
- 単一 `dev`、`ap-northeast-1`

## 運用ルール（エージェント向け）

- ユーザー向け文書・PR 本文は日本語
- 複数ステップの実装は親が抱え込まず `implement-with-subagent` → `implementation-worker`
- 実装完了後の **WBS ステータス更新と PR 操作は親**が行う
- `docs/**` 等を含む **PR 新規作成直前**に設計資料レビュー
- 進捗は `docs/wbs.md` を更新

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
次は W-200 の PR マージ後、W-210 系（または W-109）。
W-200 スペック: docs/superpowers/specs/2026-08-07-phase2-http-api-health-design.md
```
