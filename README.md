# 勤怠管理アプリ（AWS学習用）

Next.js + API Gateway + Lambda + Cognito + RDS + S3 による勤怠管理アプリの学習リポジトリです。

## ドキュメント

| 資料 | パス |
|------|------|
| 要件定義 | [docs/requirements.md](docs/requirements.md) |
| 設計スペック | [docs/superpowers/specs/2026-08-05-attendance-aws-design.md](docs/superpowers/specs/2026-08-05-attendance-aws-design.md) |
| システム構成図 | [docs/architecture/system-overview.drawio](docs/architecture/system-overview.drawio) |
| ネットワーク構成図 | [docs/architecture/network.drawio](docs/architecture/network.drawio) |
| シーケンス | [docs/architecture/sequences.md](docs/architecture/sequences.md) |
| ER図 | [docs/data/er-diagram.md](docs/data/er-diagram.md) |
| API (OpenAPI) | [docs/api/openapi.yaml](docs/api/openapi.yaml) |
| 画面一覧 | [docs/ui/screens.md](docs/ui/screens.md) |
| Terraform 設計 | [docs/infra/terraform-design.md](docs/infra/terraform-design.md) |
| AWS 認証ブートストラップ | [docs/infra/aws-auth-bootstrap.md](docs/infra/aws-auth-bootstrap.md) |
| CI/CD 設計 | [docs/cicd/github-actions.md](docs/cicd/github-actions.md) |
| 監視設計 | [docs/ops/monitoring.md](docs/ops/monitoring.md) |
| Phase 1 実装計画 | [docs/plans/2026-08-05-phase1-terraform-foundation.md](docs/plans/2026-08-05-phase1-terraform-foundation.md) |
| Phase 2 設計（HTTP API + health） | [docs/superpowers/specs/2026-08-07-phase2-http-api-health-design.md](docs/superpowers/specs/2026-08-07-phase2-http-api-health-design.md) |
| Phase 2 実装計画 | [docs/superpowers/plans/2026-08-07-phase2-http-api-health.md](docs/superpowers/plans/2026-08-07-phase2-http-api-health.md) |
| Phase 3 設計（勤怠 API） | [docs/superpowers/specs/2026-08-07-phase3-attendance-api-design.md](docs/superpowers/specs/2026-08-07-phase3-attendance-api-design.md) |
| Phase 3 実装計画 | [docs/superpowers/plans/2026-08-07-phase3-attendance-api.md](docs/superpowers/plans/2026-08-07-phase3-attendance-api.md) |
| Phase 4 設計（休暇 API） | [docs/superpowers/specs/2026-08-07-phase4-leave-api-design.md](docs/superpowers/specs/2026-08-07-phase4-leave-api-design.md) |
| Phase 4 実装計画 | [docs/superpowers/plans/2026-08-07-phase4-leave-api.md](docs/superpowers/plans/2026-08-07-phase4-leave-api.md) |
| Phase 5 設計（ユーザー API） | [docs/superpowers/specs/2026-08-07-phase5-users-api-design.md](docs/superpowers/specs/2026-08-07-phase5-users-api-design.md) |
| Phase 5 実装計画 | [docs/superpowers/plans/2026-08-07-phase5-users-api.md](docs/superpowers/plans/2026-08-07-phase5-users-api.md) |
| Phase 6 設計（エクスポート API） | [docs/superpowers/specs/2026-08-07-phase6-exports-api-design.md](docs/superpowers/specs/2026-08-07-phase6-exports-api-design.md) |
| Phase 6 実装計画 | [docs/superpowers/plans/2026-08-07-phase6-exports-api.md](docs/superpowers/plans/2026-08-07-phase6-exports-api.md) |
| Phase 7 設計（フロント + Amplify） | [docs/superpowers/specs/2026-08-07-phase7-frontend-amplify-design.md](docs/superpowers/specs/2026-08-07-phase7-frontend-amplify-design.md) |
| Phase 7 実装計画 | [docs/superpowers/plans/2026-08-07-phase7-frontend-amplify.md](docs/superpowers/plans/2026-08-07-phase7-frontend-amplify.md) |
| 作業一覧（WBS） | [docs/wbs.md](docs/wbs.md) |
| ハンドオフ（新スレッド用） | [docs/handoff.md](docs/handoff.md) |

## 設計資料レビュー

設計資料の要件漏れ・矛盾・誤字を確認するときは、チャットで「設計資料をレビューして」と依頼するか `/review-design-docs` を使います。メインエージェントは起動のみ行い、readonly の `design-doc-reviewer` サブエージェントが `docs/` を横断して指摘リストを返します（定義: [`.cursor/skills/review-design-docs/`](.cursor/skills/review-design-docs/) / [`.cursor/agents/design-doc-reviewer.md`](.cursor/agents/design-doc-reviewer.md)）。

設計関連ファイルを含む **PR を新規作成する直前** にも、ルール [`.cursor/rules/pr-design-review.mdc`](.cursor/rules/pr-design-review.mdc) により同じレビューを走らせます（ファイル変更の都度ではありません）。

### 実装の委譲

複数ステップの実装（WBS・`infra/` / `backend/` / `frontend/`）は、親のコンテキスト圧迫を避けるため `implementation-worker` サブエージェントへ委譲します（[`.cursor/skills/implement-with-subagent/`](.cursor/skills/implement-with-subagent/) / [`.cursor/agents/implementation-worker.md`](.cursor/agents/implementation-worker.md) / ルール [`.cursor/rules/delegate-implementation.mdc`](.cursor/rules/delegate-implementation.mdc)）。PR 操作と WBS ステータス更新は親が行います。

## 技術スタック（確定）

- Frontend: Next.js 14 (App Router) / TypeScript / Amplify Hosting
- Backend: Python Lambda（ドメイン別）+ API Gateway HTTP API
- Auth: Amazon Cognito（管理者招待のみ）
- DB: RDS PostgreSQL（プライベートサブネット）
- Storage: S3（CSVエクスポート）
- IaC: Terraform / CI: GitHub Actions (OIDC) / Ops: CloudWatch

## リポジトリ構成（予定）

```text
docs/       # 設計資料
infra/      # Terraform（Phase 1）
backend/    # Lambda (Python)
frontend/   # Next.js
.github/workflows/
```

Infra の使い方は [infra/README.md](infra/README.md) を参照。
