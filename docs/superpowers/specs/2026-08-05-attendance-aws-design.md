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
| ネットワーク | VPC 内完結（Lambda / RDS プライベート） |
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
- CORS: Amplify オリジンのみ

### 4.3 Lambda（Python）

| 関数 | 責務 |
|------|------|
| `attendance` | 打刻・履歴・月次サマリ |
| `leave` | 休暇申請・承認／却下・一覧 |
| `users` | 招待・一覧・更新・Cognito 同期 |
| `exports` | CSV 生成 → S3 → 署名付き URL |

共通: VPC 配置、Secrets Manager から DB 接続情報取得、構造化 JSON ログ。

### 4.4 Cognito

- User Pool（セルフサインアップ無効）
- Groups: `employee`, `manager`, `admin`
- アプリクライアント（SPA / Amplify 向け）

### 4.5 RDS PostgreSQL

- `db.t4g.micro`、シングル AZ、プライベートサブネット
- 認証情報は Secrets Manager
- 主要テーブル: `users`, `attendance_records`, `leave_requests`, `export_jobs`

### 4.6 S3

- エクスポート専用バケット
- Block Public Access
- 短命の署名付き URL でダウンロード

## 5. 認可モデル

1. API Gateway で JWT 検証（未認証は 401）
2. Lambda で Cognito Groups ＋ DB の `users.role` / `manager_id` を確認
3. 他者データへのアクセスは manager（配下のみ）または admin

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
3. HTTP API + JWT + health
4. 勤怠コア
5. 休暇・承認
6. ユーザー管理
7. エクスポート
8. フロント + Amplify
9. CI/CD 完成
10. 監視仕上げ

## 9. 関連ドキュメント

- [要件定義](../../requirements.md)
- [ER 図](../../data/er-diagram.md)
- [OpenAPI](../../api/openapi.yaml)
- [画面一覧](../../ui/screens.md)
- [シーケンス](../../architecture/sequences.md)
- [Terraform 設計](../../infra/terraform-design.md)
- [CI/CD 設計](../../cicd/github-actions.md)
- [監視設計](../../ops/monitoring.md)
