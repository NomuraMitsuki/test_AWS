# 勤怠管理アプリ — 設計スペック

**日付**: 2026-08-05  
**ステータス**: Approved（ブレインストーム合意）  
**リージョン**: `ap-northeast-1`

## 1. 背景と目的

個人学習として、AWS マネージドサービス中心の勤怠管理アプリを構築する。フロントは Amplify、API は API Gateway + Lambda、認証は Cognito、永続化は RDS PostgreSQL、成果物配信は S3。インフラは Terraform、配信は GitHub Actions、運用は CloudWatch で揃える。

## 2. 合意した前提

| 項目 | 決定 |
|------|------|
| MVP 範囲 | 標準（打刻・休暇承認・ユーザー管理・CSV） |
| フロント宿主 | Amplify Hosting |
| ネットワーク | Lambda / RDS は VPC プライベート配置。Amplify・API Gateway・Cognito・S3 等のマネージドサービスは VPC 外 |
| 環境数 | dev 単一 |
| ユーザー登録 | 管理者招待のみ |
| API 構成 | ドメイン別 Lambda + HTTP API（案1） |

## 3. アーキテクチャ概要

```text
Browser
  → Amplify (Next.js 14)
      → Cognito (認証)
      → API Gateway HTTP API
          → JWT Authorizer (Cognito)
          → Lambda: attendance | leave | users | exports
              → RDS PostgreSQL (private)
              → S3 (exports のみ)
              → Cognito Admin API (users)
              → CloudWatch (logs/metrics)
```

詳細図: [docs/architecture/system-overview.drawio](../../architecture/system-overview.drawio)  
ネットワーク図: [docs/architecture/network.drawio](../../architecture/network.drawio)

## 4. コンポーネント責務

### 4.1 Frontend (`frontend/`)

- App Router による画面・認証セッション
- API Gateway へ Bearer JWT 付きで呼び出し
- ロールに応じた導線（employee / manager / admin）

### 4.2 API Gateway

- HTTP API
- Cognito JWT Authorizer
- ルートをドメイン別 Lambda にマッピング
- CORS: Amplify オリジンを許可。ローカル開発例外として `http://localhost:3000` も許可（詳細: [Phase 7](2026-08-07-phase7-frontend-amplify-design.md)）

### 4.3 Lambda（Python）

| 関数 | 責務 |
|------|------|
| `attendance` | 打刻・履歴・月次サマリ |
| `leave` | 休暇申請・承認／却下・一覧 |
| `users` | 招待・一覧・更新・Cognito 同期 |
| `exports` | CSV 生成 → S3 → 署名付き URL |
| `health` | 稼働確認のみ（`GET /health`）。JWT 不要・**VPC 外**（DB 非接続） |
| `migrate` | RDS へ SQL `001`〜`003` を適用し、任意で初回 admin の `users` INSERT。**HTTP 非公開**・VPC 内・手動 `aws lambda invoke`（[Phase 11](2026-08-17-phase11-migrate-admin-design.md)） |

ドメイン Lambda（attendance / leave / users / exports）共通: VPC 配置、Secrets Manager から DB 接続情報取得、構造化 JSON ログ。`health` は例外（VPC 外）。`migrate` も VPC 内・DB secret 読取だが API Gateway には繋がない。詳細: [Phase 2 スペック](2026-08-07-phase2-http-api-health-design.md)、[Phase 11](2026-08-17-phase11-migrate-admin-design.md)。

### 4.4 Cognito

- User Pool（セルフサインアップ無効）
- Groups: `employee`, `manager`, `admin`
- アプリクライアント（SPA / Amplify 向け）

### 4.4.1 最初の admin ブートストラップ

アプリの `POST /users`（招待）は JWT 付き admin が前提のため、**最初の1人は手動で作る**。

1. AWS コンソールまたは CLI で Cognito User Pool にユーザーを作成し、グループ `admin` に追加する（仮パスワード発行）
2. RDS の `users` に同じメール／`cognito_sub`／`role=admin`／`status=active` の行を挿入する（マイグレーション直後。到達手段は [Phase 11](2026-08-17-phase11-migrate-admin-design.md) の migrate Lambda invoke）
3. その admin でログインし、以降のユーザーはアプリの招待画面から作成する

Terraform での完全自動シードは学習コストを上げるため必須としない。Cognito 側の手順は本節と要件定義、RDS 到達は Phase 11 / [aws-auth-bootstrap.md](../../infra/aws-auth-bootstrap.md) §E を正とする。

### 4.5 RDS PostgreSQL

- `db.t4g.micro`、シングル AZ、プライベートサブネット
- 認証情報は Secrets Manager
- 主要テーブル: `users`, `attendance_records`, `leave_requests`, `export_jobs`

### 4.6 S3

- エクスポート専用バケット
- Block Public Access
- 短命の署名付き URL でダウンロード

## 5. 認可モデル

1. API Gateway で JWT 検証（未認証は 401）。例外は `GET /health` のみ
2. Lambda で Cognito Groups ＋ DB の `users.role` / `manager_id` を確認
3. 他者データへのアクセスは manager（配下のみ）または admin
4. 一覧・エクスポートの `scope` は `self` / `team` / `all` で統一する

## 6. エラーモデル

共通レスポンス:

```json
{
  "code": "ALREADY_CLOCKED_IN",
  "message": "本日は既に出勤打刻済みです",
  "request_id": "..."
}
```

業務エラーは 4xx、予期せぬ障害は 5xx（CloudWatch アラーム対象）。

## 7. リポジトリ構成

```text
docs/           # 設計資料
infra/          # Terraform
backend/        # Python Lambda
frontend/       # Next.js 14
.github/workflows/
```

## 8. 実装フェーズ

1. 設計資料（本 Phase 0）
2. Terraform 基盤（VPC / RDS / Cognito / S3 / CW）
3. HTTP API + JWT + health — [Phase 2 スペック](2026-08-07-phase2-http-api-health-design.md) / [実装計画](../plans/2026-08-07-phase2-http-api-health.md)（W-200）
4. 勤怠コア — [Phase 3 スペック](2026-08-07-phase3-attendance-api-design.md) / [実装計画](../plans/2026-08-07-phase3-attendance-api.md)（W-210）
5. 休暇・承認 — [Phase 4 スペック](2026-08-07-phase4-leave-api-design.md) / [実装計画](../plans/2026-08-07-phase4-leave-api.md)（W-220）
6. ユーザー管理 — [Phase 5 スペック](2026-08-07-phase5-users-api-design.md) / [実装計画](../plans/2026-08-07-phase5-users-api.md)（W-230）
7. エクスポート — [Phase 6 スペック](2026-08-07-phase6-exports-api-design.md) / [実装計画](../plans/2026-08-07-phase6-exports-api.md)（W-240）
8. フロント + Amplify — [Phase 7 スペック](2026-08-07-phase7-frontend-amplify-design.md)（W-250）。実装計画は同 Phase の plans を参照
9. CI/CD 完成 — [Phase 8 スペック](2026-08-07-phase8-cicd-workflows-design.md)（W-260）
10. 監視仕上げ — [Phase 9 スペック](2026-08-10-phase9-monitoring-polish-design.md)（W-270）
11. リモート state / Secrets / CI plan — [Phase 10 スペック](2026-08-17-phase10-w109-remote-state-design.md)（W-109）
12. RDS マイグレーション / 初回 admin — [Phase 11 スペック](2026-08-17-phase11-migrate-admin-design.md)（W-280）

## 9. 関連ドキュメント

- [要件定義](../../requirements.md)
- [ER 図](../../data/er-diagram.md)
- [OpenAPI](../../api/openapi.yaml)
- [画面一覧](../../ui/screens.md)
- [シーケンス](../../architecture/sequences.md)
- [Terraform 設計](../../infra/terraform-design.md)
- [CI/CD 設計](../../cicd/github-actions.md)
- [監視設計](../../ops/monitoring.md)
- [Phase 2 HTTP API + health 設計](2026-08-07-phase2-http-api-health-design.md)
- [Phase 3 勤怠 API 設計](2026-08-07-phase3-attendance-api-design.md)
- [Phase 4 休暇 API 設計](2026-08-07-phase4-leave-api-design.md)
- [Phase 5 ユーザー API 設計](2026-08-07-phase5-users-api-design.md)
- [Phase 6 エクスポート API 設計](2026-08-07-phase6-exports-api-design.md)
- [Phase 7 フロント + Amplify 設計](2026-08-07-phase7-frontend-amplify-design.md)
- [Phase 8 CI/CD ワークフロー設計](2026-08-07-phase8-cicd-workflows-design.md)
- [Phase 9 監視仕上げ設計](2026-08-10-phase9-monitoring-polish-design.md)
- [Phase 10 リモート state / W-109 設計](2026-08-17-phase10-w109-remote-state-design.md)
- [Phase 11 マイグレーション / 初回 admin 設計](2026-08-17-phase11-migrate-admin-design.md)
