# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-07（W-109 を API／フロント完了後まで延期）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform と W-200（HTTP API + health）まで `main` 済み（AWS リソースは destroy 済み）。**次は W-210（勤怠 API）**。W-109（GitHub Secrets / OIDC）は API・フロント完了まで着手しない。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: **`main`**
- 直近マージ: PR #1〜#8

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, **W-200 完了**（apply なし）
- Terraform Phase 1 + Phase 2（health / HTTP API / JWT authorizer）コード
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`
- AWS リソースは確認後 **destroy 済み**

## 次にやること（優先順）

1. **W-210**: 勤怠 API（打刻・履歴・サマリ）。実装は `implementation-worker` へ委譲
2. **W-220〜W-250**: 休暇・ユーザー・エクスポート・フロント
3. **W-109**: **API（W-210〜）およびフロント（W-250）完了後**に再 apply → GitHub Secrets / OIDC CI（それまで着手しない）

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
- **W-109 を API／フロント完了前に進めない**

## 新スレッドへの貼り付け例

```text
@docs/handoff.md と @docs/wbs.md を読んで作業を引き継いでください。
実装はサブエージェント（implementation-worker）へ委譲してください。
次は W-210。W-109 は API・フロント完了まで着手しない。
```
