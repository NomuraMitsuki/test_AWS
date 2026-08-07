# ハンドオフ — 新スレッド引き継ぎ用

最終更新: 2026-08-07（W-230 ユーザー API 実装後。次は W-240）

## 一言で

AWS 学習用の勤怠管理アプリ。Phase 1 Terraform、W-200（HTTP API + health）、W-210（勤怠 API）、W-220（休暇 API）、**W-230（ユーザー管理 API）** までコード実装済み（apply なし）。**次は W-240（エクスポート API）**。W-109（GitHub Secrets / OIDC）は API・フロント完了まで着手しない。

## リポジトリ

- GitHub: `NomuraMitsuki/test_AWS`
- 作業ブランチ: **`main`**（W-230 は `cursor/w230-users-api-a099` で実装）
- 直近マージ: PR #1〜#11

## 完了していること

- 設計資料一式（`docs/`）
- 設計レビュー担当 / 日本語ルール / PR 作成時レビュー
- **実装委譲**: skill `implement-with-subagent` + agent `implementation-worker` + rule `delegate-implementation`（W-006）
- WBS: W-001〜020, W-100〜108, W-006, W-200、W-210、W-220、**W-230 実装完了（apply なし・WBS ステータスは親が更新）**
- Terraform Phase 1〜5（attendance / leave / users Lambda / JWT ルート）コード
- backend: `health` + `attendance` + `leave` + `users`（pytest）+ `migrations/001_init_attendance.sql` + `002_leave_requests.sql`
- **認証手順**: [docs/infra/aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md)
- **一括スクリプト**: `./infra/scripts/tf-dev.sh`
- AWS リソースは確認後 **destroy 済み**（再 apply は未実施）

## 次にやること（優先順）

1. **W-240**: エクスポート API。実装は `implementation-worker` へ委譲
2. **W-250**: フロント
3. **W-109**: **API（W-210〜）およびフロント（W-250）完了後**に再 apply → GitHub Secrets / OIDC CI（それまで着手しない）

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
次は W-240。W-109 は API・フロント完了まで着手しない。
```
