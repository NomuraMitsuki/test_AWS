# Phase 9 — CloudWatch ダッシュボード・アラーム仕上げ設計（W-270）

**日付**: 2026-08-10  
**ステータス**: Approved（apply なしで実装）  
**WBS**: W-270  
**監視正本**: [docs/ops/monitoring.md](../../ops/monitoring.md)

## 1. ゴール

Phase 1 の monitoring 骨格を、`monitoring.md` どおりのダッシュボード＋主要アラームに仕上げ、`terraform validate` まで通す。**apply は行わない。**

## 2. 非ゴール

- terraform apply / 実アラーム発火 E2E
- W-109（Secrets / 再 apply）
- API Gateway アクセスログの本格整備（本 Phase はメトリクス＋Lambda エラーログに限定）
- Lambda ロググループの保持期間（14 日）の Terraform 管理 — 後続可。本 Phase は既存／実行時作成グループをダッシュボードが名前参照する
- 過剰なカスタムメトリクス、外部オンコール連携

## 3. 方針（採用案 A）

`infra/modules/monitoring` を拡張し、`envs/dev` から API ID・Lambda 関数名・RDS インスタンス ID を渡す。SNS トピックは既存を流用。

## 4. ダッシュボード

名前: `${name_prefix}-overview`（例: `attendance-dev-overview`）

| 領域 | ウィジェット |
|------|----------------|
| API | HTTP API の Count / 4xx / 5xx / Latency（`ApiId`） |
| Lambda | health / attendance / leave / users / exports の Invocations / Errors / Duration |
| RDS | CPUUtilization / DatabaseConnections / FreeStorageSpace |
| ログ | 各 Lambda の ERROR ログウィジェット（`/aws/lambda/<function_name>`） |

## 5. アラーム

| アラーム | 条件（初期値） | 通知 |
|----------|----------------|------|
| Lambda Errors（関数ごと×5） | Errors > 0 が 1 分×3 | SNS |
| API 5XX | 5xx ≥ 5 / 5 分 | SNS |
| API Latency p99 | p99 > 3000ms / 5 分 | SNS |
| RDS CPU | CPUUtilization > 80% / 10 分 | SNS |
| RDS Connections | DatabaseConnections > 40 / 10 分（正本 `monitoring.md` の初期値として実装時に同期） | SNS |

- SNS: 既存 `${name_prefix}-alarms`
- `alarm_email` が空なら購読なし（トピック＋アラームは作成）

## 6. 配線

`monitoring` 変数（追加）:

- `http_api_id` ← `module.api.http_api_id`
- `lambda_function_names`（map または 5 個別）← api の各 `*_lambda_function_name`
- `db_instance_id` ← `module.data.db_instance_id`（出力名に合わせる）

`infra/envs/dev`: `module.api` / `module.data` の出力を渡す。monitoring は api / data に依存。

## 7. 検証

- `terraform fmt` / `init -backend=false` / `validate` in `infra/envs/dev`
- 実装完了時 docs: `monitoring.md`・`terraform-design.md`・handoff を同期（README 索引・親 §10 リンクは設計 PR で先行可）
- 実装計画: [plans 配下に Phase 9 計画を書く](../plans/)（スペック承認後）
- `docs/wbs.md` ステータス更新は親

## 8. 完了後

- WBS W-270 完了
- 次: **W-109**（再 apply / Secrets）が実質の残タスク（運用開始）
