# 作業一覧（WBS / TODO）

このリポジトリで進める作業の一覧。進捗に応じてステータスを更新する。

凡例: `未着手` / `進行中` / `完了` / `ブロック`

---

## 0. 設計・プロセス基盤

| ID | 作業 | ステータス | メモ |
|----|------|------------|------|
| W-001 | Phase 0 設計資料一式の作成・main マージ | 完了 | PR #1 |
| W-002 | 設計資料レビュー担当（スキル＋サブエージェント）の追加 | 進行中 | PR #2 |
| W-003 | 日本語表記ルール（`.cursor/rules`）の追加 | 進行中 | PR #2 |
| W-004 | 本 WBS の作成・維持 | 進行中 | 本ファイル |

---

## 1. 設計資料のフォローアップ（レビュー指摘）

スモークレビュー由来。実装コードより先に資料を直す想定。

| ID | 重大度 | 作業 | ステータス | 由来 |
|----|--------|------|------------|------|
| W-010 | Must | leave の `scope` 値を統一（OpenAPI の `me` と export/ER の `self`） | 未着手 | R-001 |
| W-011 | Should | manager の配下勤怠閲覧を画面・API に明記（または要件を絞って整合） | 未着手 | R-002 |
| W-012 | Should | `GET /health` の JWT 例外を要件／OpenAPI 説明で明記 | 未着手 | R-003 |
| W-013 | Should | 最初の `admin` ブートストラップ手順を資料に追記 | 未着手 | R-004 |
| W-014 | Nit | Phase 1 計画の二重配置（`docs/plans` と `docs/superpowers/plans`）を解消または役割分担を明記 | 未着手 | R-005 |
| W-015 | Nit | ER の `leave_requests(approver_id)` インデックス説明と検索パスの食い違いを修正 | 未着手 | R-006 |
| W-016 | Nit | 設計スペック「VPC 内完結」の文言を、マネージドサービスが VPC 外である旨と誤解なく揃える | 未着手 | R-007 |

---

## 2. Phase 1 — Terraform 基盤

詳細手順: [plans/2026-08-05-phase1-terraform-foundation.md](plans/2026-08-05-phase1-terraform-foundation.md)

| ID | 作業 | ステータス | メモ |
|----|------|------------|------|
| W-100 | Terraform レイアウト bootstrap（`infra/envs/dev`） | 未着手 | |
| W-101 | network モジュール（VPC / NAT / SG） | 未着手 | |
| W-102 | cognito モジュール | 未着手 | |
| W-103 | data モジュール（RDS + Secrets Manager） | 未着手 | |
| W-104 | storage モジュール（S3 exports） | 未着手 | |
| W-105 | monitoring 骨格 | 未着手 | |
| W-106 | github_oidc モジュール | 未着手 | |
| W-107 | dev 合成 + infra 用 GitHub Actions（plan まで） | 未着手 | |
| W-108 | 検証ゲート（fmt / validate / plan） | 未着手 | AWS 資格情報が必要 |

---

## 3. 以降フェーズ（設計合意済み・未着手）

| ID | 作業 | ステータス | メモ |
|----|------|------------|------|
| W-200 | HTTP API + JWT + health Lambda | 未着手 | Phase 2 |
| W-210 | 勤怠 API（打刻・履歴・サマリ） | 未着手 | |
| W-220 | 休暇申請／承認 API | 未着手 | |
| W-230 | ユーザー招待・ロール管理 API | 未着手 | W-013 と併せて admin 初期化を考慮 |
| W-240 | CSV エクスポート（S3 + 署名付き URL） | 未着手 | |
| W-250 | Next.js フロント + Amplify | 未着手 | |
| W-260 | GitHub Actions（backend / frontend）完成 | 未着手 | |
| W-270 | CloudWatch ダッシュボード・アラーム仕上げ | 未着手 | |

---

## 更新ルール

1. 新しい大きな作業が出たら ID を採番して追記する（設計フォローは `W-01x`、基盤は `W-1xx`、アプリは `W-2xx`）。
2. 設計レビューで出た Must/Should は、修正 PR を切る前に本表へ落とす。
3. 完了したらステータスを `完了` にし、関連 PR 番号をメモに残す。
