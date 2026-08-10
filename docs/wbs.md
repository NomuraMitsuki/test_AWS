# 作業一覧（WBS / TODO）

このリポジトリで進める作業の一覧。進捗に応じてステータスを更新する。

凡例: `未着手` / `進行中` / `完了` / `ブロック`

---

## 0. 設計・プロセス基盤

| ID | 作業 | ステータス | メモ |
|----|------|------------|------|
| W-001 | Phase 0 設計資料一式の作成・main マージ | 完了 | PR #1 |
| W-002 | 設計資料レビュー担当（スキル＋サブエージェント）の追加 | 完了 | PR #2 |
| W-003 | 日本語表記ルール（`.cursor/rules`）の追加 | 完了 | PR #2 |
| W-004 | 本 WBS の作成・維持 | 完了 | PR #2 で作成。以降は随時更新 |
| W-005 | PR 作成時の設計資料レビュールール追加 | 完了 | PR #3 / `pr-design-review` |
| W-006 | 実装委譲（スキル＋サブエージェント＋ルール）の追加 | 完了 | PR #7 / `implement-with-subagent` / `implementation-worker` / `delegate-implementation` |

---

## 1. 設計資料のフォローアップ（レビュー指摘）

| ID | 重大度 | 作業 | ステータス | 由来 |
|----|--------|------|------------|------|
| W-010 | Must | leave の `scope` 値を統一（OpenAPI の `me` と export/ER の `self`） | 完了 | R-001 / PR #3 |
| W-011 | Should | manager の配下勤怠閲覧を画面・API に明記 | 完了 | R-002 / PR #3 |
| W-012 | Should | `GET /health` の JWT 例外を要件／OpenAPI 説明で明記 | 完了 | R-003 / PR #3 |
| W-013 | Should | 最初の `admin` ブートストラップ手順を資料に追記 | 完了 | R-004 / PR #3 |
| W-014 | Nit | Phase 1 計画の二重配置を解消 | 完了 | R-005 / PR #3 |
| W-015 | Nit | ER の承認待ちインデックス説明を修正 | 完了 | R-006 / PR #3 |
| W-016 | Nit | 設計スペックのネットワーク文言を明確化 | 完了 | R-007 / PR #3 |
| W-017 | Should | `/attendance/me` と `/records` の役割整理 | 完了 | PR #4 |
| W-018 | Should | 休暇承認画面（S10）の一覧取得 API を明記 | 完了 | PR #4 |
| W-019 | Should | 配下サマリの画面導線（S06/S07）を揃える | 完了 | PR #4 |
| W-020 | Should | `/attendance/summary` の配下限定を OpenAPI に明記 | 完了 | PR #4 |

---

## 2. Phase 1 — Terraform 基盤

詳細手順: [plans/2026-08-05-phase1-terraform-foundation.md](plans/2026-08-05-phase1-terraform-foundation.md)

| ID | 作業 | ステータス | メモ |
|----|------|------------|------|
| W-100 | Terraform レイアウト bootstrap（`infra/envs/dev`） | 完了 | PR #4 |
| W-101 | network モジュール（VPC / NAT / SG） | 完了 | PR #4 |
| W-102 | cognito モジュール | 完了 | PR #4 |
| W-103 | data モジュール（RDS + Secrets Manager） | 完了 | PR #4 |
| W-104 | storage モジュール（S3 exports） | 完了 | PR #4 |
| W-105 | monitoring 骨格 | 完了 | PR #4 |
| W-106 | github_oidc モジュール | 完了 | PR #4 |
| W-107 | dev 合成 + infra 用 GitHub Actions（plan まで） | 完了 | PR #4 |
| W-108 | 検証ゲート（fmt / validate / plan）＋初回 apply（OIDC 用） | 完了 | PR #6。ローカルで plan/apply 成功を確認後、課金抑制のため destroy 済み |
| W-109 | GitHub Secrets（OIDC ロール ARN）登録と CI plan 有効化 | 未着手 | API・フロント完了済み。再 apply → `AWS_ROLE_ARN_INFRA` / `AWS_ROLE_ARN_BACKEND` 登録。リモート state 化も検討（[aws-auth-bootstrap.md](infra/aws-auth-bootstrap.md) §D） |

---

## 3. アプリ実装フェーズ

| ID | 作業 | ステータス | メモ |
|----|------|------------|------|
| W-200 | HTTP API + JWT + health Lambda | 完了 | PR #8。apply なし（コード + validate + pytest）。実装は implementation-worker |
| W-210 | 勤怠 API（打刻・履歴・サマリ） | 完了 | PR #10。apply なし（pytest + terraform validate）。実装は implementation-worker |
| W-220 | 休暇申請／承認 API | 完了 | PR #11。apply なし（pytest + terraform validate）。実装は implementation-worker |
| W-230 | ユーザー招待・ロール管理 API | 完了 | PR #12。apply なし（pytest + terraform validate）。実装は implementation-worker |
| W-240 | CSV エクスポート（S3 + 署名付き URL） | 完了 | PR #13。apply なし（pytest + terraform validate）。実装は implementation-worker |
| W-250 | Next.js フロント + Amplify | 完了 | PR #14。apply なし（lint / next build / terraform validate）。実装は implementation-worker。Amplify Actions デプロイは W-260 |
| W-260 | GitHub Actions（backend / frontend）完成 | 完了 | PR #15。backend.yml / frontend start-job / infra apply 骨格。Secrets 実登録は W-109。実装は implementation-worker |
| W-270 | CloudWatch ダッシュボード・アラーム仕上げ | 未着手 | Phase 9: ダッシュボード＋主要アラーム（apply なし）。設計: phase9-monitoring-polish |

---

## 更新ルール

1. 新しい大きな作業が出たら ID を採番して追記する（設計フォローは `W-01x`、基盤は `W-1xx`、アプリは `W-2xx`）。
2. 設計レビューで出た Must / Should は、修正しない場合は本表へ落としてから PR を作成する（詳細は `.cursor/rules/pr-design-review.mdc`）。
3. 完了したらステータスを `完了` にし、関連 PR 番号をメモに残す。
4. **キリのよいタイミング**（例: Phase 単位の PR マージ後）でチャットコンテキストを `/summarize` するとよい。
