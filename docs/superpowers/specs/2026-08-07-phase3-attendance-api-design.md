# Phase 3 — 勤怠 API 設計（W-210）

**日付**: 2026-08-07  
**ステータス**: Approved（W-200 と同様 apply なしで実装開始）  
**WBS**: W-210  
**親スペック**: [2026-08-05-attendance-aws-design.md](2026-08-05-attendance-aws-design.md)  
**API 正本**: [docs/api/openapi.yaml](../../api/openapi.yaml)  
**ER**: [docs/data/er-diagram.md](../../data/er-diagram.md)

## 1. ゴール

JWT 必須の勤怠 API（打刻・履歴・月次サマリ）を Python Lambda + Terraform ルートで実装し、単体テストと `terraform validate` まで通す。

**本 Phase では apply / 実デプロイは行わない。**

## 2. 非ゴール

- 休暇・ユーザー管理・エクスポート API（W-220〜）
- フロント（W-250）
- W-109（GitHub Secrets）
- apply / E2E against live RDS

## 3. エンドポイント

| Method | Path | 備考 |
|--------|------|------|
| POST | `/attendance/clock-in` | 201 / 409 |
| POST | `/attendance/clock-out` | 200 / 409 |
| GET | `/attendance/records` | `scope=self\|team\|all` |
| GET | `/attendance/me` | `records?scope=self` のエイリアス |
| GET | `/attendance/summary` | year/month 必須 |

すべて Cognito JWT 必須（API Gateway JWT authorizer）。

## 4. 認可（Lambda 内）

- JWT claims の `sub` / email / Cognito groups を読む
- DB `users` と突合（なければ 403 またはブートストラップ前提でテスト用モック）
- `scope=self`: 本人のみ
- `scope=team`: manager かつ `users.manager_id = 自分`
- `scope=all`: admin のみ
- summary の他者 `user_id`: manager は配下のみ、admin は任意

## 5. データ

- SQL マイグレーション（リポジトリ同梱）: `users`, `attendance_records`（ER 準拠）
- 1 日 1 レコード UNIQUE `(user_id, work_date)`（JST の勤務日）
- 打刻競合は 409 + 共通エラー形式 `{code, message, request_id}`

## 6. 構成

```text
backend/
  attendance/          # Lambda ハンドラ + ドメインロジック
  shared/              # 任意: レスポンスヘルパ（health と共有しすぎない）
  migrations/001_*.sql
  tests/
infra/modules/api/     # attendance Lambda（VPC）+ JWT 付きルート追加
```

- attendance Lambda: Python 3.12、**VPC 内**、Secrets Manager から DB 接続
- health は VPC 外のまま

## 7. 検証

- pytest（DB はモックまたは sqlite/フェイク層。実 RDS 不要）
- `terraform fmt` / `validate`
- apply なし
