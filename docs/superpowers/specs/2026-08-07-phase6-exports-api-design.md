# Phase 6 — CSV エクスポート API 設計（W-240）

**日付**: 2026-08-07  
**ステータス**: Approved（apply なしで実装）  
**WBS**: W-240  
**API 正本**: [docs/api/openapi.yaml](../../api/openapi.yaml)  
**シーケンス**: [docs/architecture/sequences.md](../../architecture/sequences.md) §4

## 1. ゴール

`POST /exports/attendance` を exports Lambda + S3（署名付き URL）で実装し、pytest と `terraform validate` まで通す。**apply は行わない。**

## 2. 非ゴール

- フロント・W-109 / apply / 実 S3 E2E
- 非同期ジョブキュー（本 Phase は同期で CSV 生成→Put→presign）

## 3. エンドポイント

| Method | Path | 備考 |
|--------|------|------|
| POST | `/exports/attendance` | JWT 必須。body: from_date, to_date, scope |

認可の `scope` は勤怠一覧と同じ（self / team / all）。employee は self のみ。未登録・disabled → 403。

## 4. 処理

1. `export_jobs` に pending を INSERT
2. 権限内の `attendance_records` を取得し CSV 生成
3. S3 PutObject（exports バケット）
4. 署名付き URL 生成（短命、例: 300 秒）
5. job を completed に更新し 200 `{ export_job_id, download_url, expires_in }`
6. 失敗時は job を failed にしうる（テストで検証可能な範囲）

S3 / 署名 URL は境界 IF でモック可能にする。

## 5. 構成

```text
backend/exports/
backend/migrations/003_export_jobs.sql
infra/modules/api/  # exports Lambda（VPC）+ JWT ルート + S3 Put/Presign IAM
```

## 6. 検証

- pytest（インメモリ + S3 モック）
- terraform fmt / validate
