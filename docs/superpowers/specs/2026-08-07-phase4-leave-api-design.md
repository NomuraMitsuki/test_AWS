# Phase 4 — 休暇申請／承認 API 設計（W-220）

**日付**: 2026-08-07  
**ステータス**: Approved（apply なしで実装）  
**WBS**: W-220  
**API 正本**: [docs/api/openapi.yaml](../../api/openapi.yaml)  
**ER**: [docs/data/er-diagram.md](../../data/er-diagram.md)

## 1. ゴール

JWT 必須の休暇 API（一覧・作成・承認・却下）を leave Lambda + Terraform ルートで実装し、pytest と `terraform validate` まで通す。**apply は行わない。**

## 2. 非ゴール

- ユーザー管理・エクスポート・フロント
- W-109 / apply / 実 RDS E2E

## 3. エンドポイント

| Method | Path | 備考 |
|--------|------|------|
| GET | `/leave-requests` | `scope` + optional `status`。employee は self のみ |
| POST | `/leave-requests` | 201 / 400（日付不正）/ 401 / 403 |
| POST | `/leave-requests/{id}/approve` | manager（配下）/ admin。pending のみ。無しは 404、非 pending は 409 |
| POST | `/leave-requests/{id}/reject` | 同上。optional `reject_reason` |

すべて Cognito JWT 必須。

## 4. 認可

- ロール正は DB `users.role`（attendance と同様）
- `scope=self` / `team` / `all` は勤怠 API と同じ規則
- 承認・却下: manager は申請者の `manager_id` が自分、admin は全体。employee は 403
- 未登録・disabled → 403

## 5. 業務ルール

- 作成時 `status=pending`
- 承認/却下は `pending` のみ（それ以外 409）
- `leave_type`: `paid` / `absence` / `other`
- `start_date` ≤ `end_date`（違反は 400）

## 6. 構成

```text
backend/leave/           # Lambda
backend/migrations/002_leave_requests.sql
infra/modules/api/       # leave Lambda（VPC）+ JWT ルート
```

## 7. 検証

- pytest（インメモリリポジトリ）
- terraform fmt / validate
- apply なし
