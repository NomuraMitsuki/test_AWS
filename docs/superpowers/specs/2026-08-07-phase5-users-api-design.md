# Phase 5 — ユーザー招待・ロール管理 API 設計（W-230）

**日付**: 2026-08-07  
**ステータス**: Approved（apply なしで実装）  
**WBS**: W-230  
**API 正本**: [docs/api/openapi.yaml](../../api/openapi.yaml)  
**ブートストラップ**: 親スペック §4.4.1

## 1. ゴール

admin 向けユーザー一覧・招待・更新 API を users Lambda + Terraform で実装し、pytest と `terraform validate` まで通す。**apply は行わない。**

## 2. 非ゴール

- エクスポート・フロント・W-109 / apply
- Cognito 実呼び出しの E2E（テストは Cognito クライアントをモック）
- Terraform による最初の admin 自動シード（手動手順は親スペック §4.4.1 のまま）

## 3. エンドポイント

| Method | Path | 認可 | 備考 |
|--------|------|------|------|
| GET | `/users` | admin | 一覧 |
| POST | `/users` | admin | 招待。メール重複は 409 |
| PATCH | `/users/{id}` | admin | role / manager_id / status。無しは 404 |

JWT 必須。employee / manager は 403。

admin 判定の正は DB `users.role=admin`（Cognito groups は補助）。未登録または `status=disabled` は 403（Phase 3 と同じ）。

## 4. 招待フロー（本番想定）

1. Cognito `AdminCreateUser`（仮パスワード）+ グループ付与
2. RDS `users` に行を作成（`cognito_sub`, email, name, role, manager_id, status=active）
3. 失敗時は可能な範囲でロールバック方針をサービス内で簡潔に（テストではモック）

## 5. 更新

- `role`: employee / manager / admin（Cognito group 同期は本番パスでモック可能な IF）
- `manager_id`: UUID or null
- `status`: active / disabled

## 6. 構成

```text
backend/users/
backend/migrations/003_users_bootstrap_note.sql  # 任意コメント／制約補強。users 表は 001 済みなら不要な変更のみ
infra/modules/api/  # users Lambda（VPC）+ JWT ルート + Cognito admin IAM（スタブポリシー可）
```

001 で users 表がある場合、追加マイグレーションはインデックス等の最小に留める。

## 7. 検証

- pytest（インメモリ DB + Cognito モック）
- terraform fmt / validate
