# 運用・監視設計 — CloudWatch

## 目的

学習環境でも「壊れたら気づける」状態を作る。過剰なアラートは避け、少数の重要アラームに絞る。

## ログ

| ソース | Log group（案） | 保持 |
|--------|------------------|------|
| Lambda attendance/leave/users/exports | `/aws/lambda/attendance-dev-*` | 14 日 |
| API Gateway アクセスログ | `/aws/apigateway/attendance-dev` | 14 日 |

Lambda は JSON 構造化ログ（`level`, `message`, `request_id`, `user_sub` など）。  
PII（メール全文など）は必要最小限。パスワードは絶対に出さない。

## メトリクスとアラーム

| アラーム | 条件（初期値） | 意味 |
|----------|----------------|------|
| Lambda Errors | エラー > 0 が 1 分×3 | 関数障害 |
| API 5XX | 5xx count >= 5 / 5 分 | API 異常 |
| API Latency p99 | p99 > 3000ms / 5 分 | 遅延（VPC Cold start 含む） |
| RDS CPU | CPUUtilization > 80% / 10 分 | DB 過負荷 |
| RDS Connections | DatabaseConnections が高い状態が継続 | 接続枯渇の兆候 |

通知先: SNS トピック → 学習用メール（任意）。未設定でもアラーム作成までは行う。

## ダッシュボード

名前: `attendance-dev-overview`

ウィジェット案:

1. API Gateway: 4xx / 5xx / count / latency
2. Lambda: invocations / errors / duration（関数別）
3. RDS: CPU / connections / free storage
4. 最近の Lambda エラーログ（ログウィジェット）

## ランブック（簡易）

### Lambda エラー急増

1. ダッシュボードで対象関数を特定
2. Log group で `level=ERROR` を絞る
3. `request_id` で API Gateway ログと突合
4. 典型原因: DB 接続失敗（Secrets/SG/NAT）、JWT クレーム不足、タイムアウト

### API 5xx

1. 統合先 Lambda のエラー有無を確認
2. Authorizer 失敗は通常 401 — 5xx なら Lambda/統合設定を疑う
3. 直近デプロイの rollback

### RDS 接続不能

1. Lambda SG → RDS SG の 5432 を確認
2. Secrets Manager の値と RDS エンドポイントの一致
3. NAT / VPC endpoint 経由で Secrets に届いているか（プライベート Lambda）

## バックアップ・復旧（学習用）

- RDS 自動バックアップ（保持 7 日）
- `terraform destroy` 前に必要なデータはエクスポート
- S3 エクスポートオブジェクトは lifecycle で 30 日削除（任意）
