# 要件定義書 — 勤怠管理アプリ（AWS学習用）

## 1. 目的

AWS の主要サービス（Lambda・API Gateway・Cognito・RDS・S3）と、Terraform・GitHub Actions・CloudWatch を用いた勤怠管理 Web アプリを構築し、実務に近い構成で各技術の理解を深める。

## 2. ステークホルダーとロール

| ロール | Cognito Group | 概要 |
|--------|---------------|------|
| 一般社員 | `employee` | 自身の打刻・履歴・休暇申請・自身データの CSV 出力 |
| 上長 | `manager` | employee 権限 ＋ 配下メンバーの休暇承認・勤怠閲覧 |
| 管理者 | `admin` | ユーザー招待／無効化、ロール割当、全体レポート・CSV |

上長関係は `users.manager_id` による **1段のみ**（組織階層の多段は MVP 外）。

## 3. スコープ（MVP）

### 3.1 含む機能

- 管理者によるユーザー招待（セルフサインアップなし）
- 初回ログイン時の仮パスワード変更
- 出勤／退勤打刻
- 自身の打刻履歴・月次勤務時間サマリ
- 休暇申請（有給／欠勤／その他）と上長による承認／却下
- 管理者のユーザー一覧・招待・無効化・ロール変更
- 勤怠 CSV のエクスポート（S3 ＋ 署名付き URL）
- ダッシュボード（本日の打刻状態、承認待ち件数）

### 3.2 含まない機能（MVP 外）

- 残休暇日数マスタ・自動消化
- シフト／勤務パターン
- 残業申請・打刻修正申請
- メール／プッシュ通知
- Multi-AZ RDS、WAF、高度な監査ログ
- 多環境（staging / prod）— 設計上は後から追加可能とする

## 4. 業務ルール

1. タイムゾーンは `Asia/Tokyo`
2. 1 日あたり出勤→退勤は 1 セット。未退勤のまま再出勤不可
3. 退勤は当日（または直近）の未退勤レコードに対してのみ可能
4. 休暇申請は `pending` → `approved` / `rejected` のみ
5. 承認操作は申請者の `manager_id` に紐づく上長、または `admin` のみ
6. ユーザー登録は管理者が Cognito に作成し、アプリ DB の `users` と同期する

## 5. 非機能要件

| 項目 | 内容 |
|------|------|
| 環境 | 単一 `dev`（`ap-northeast-1`） |
| 可用性 | 学習用。シングル AZ RDS、NAT Gateway 1 つ |
| セキュリティ | API は Cognito JWT 必須。RDS 非公開。S3 は公開禁止 |
| 観測性 | CloudWatch Logs / Metrics / Alarms / 簡易ダッシュボード |
| コスト | 学習用途。`db.t4g.micro`、不要リソースは最小化 |
| 言語 | UI・ドキュメントは日本語。コード識別子は英語 |

## 6. 技術スタック

| 層 | 技術 |
|----|------|
| フロント | Next.js 14（App Router）/ TypeScript / Amplify Hosting |
| API | Amazon API Gateway（HTTP API） |
| コンピュート | AWS Lambda（Python）ドメイン別 4 関数 |
| 認証 | Amazon Cognito User Pool ＋ Groups |
| DB | Amazon RDS（PostgreSQL）プライベートサブネット |
| ストレージ | Amazon S3（エクスポート） |
| IaC | Terraform |
| CI/CD | GitHub Actions（OIDC） |
| 監視 | Amazon CloudWatch |

## 7. 成功基準

- 設計資料一式が `docs/` に揃い、実装の判断材料になる
- 管理者がユーザーを招待し、社員が打刻・休暇申請でき、上長が承認できる
- CSV が S3 に出力され、署名付き URL で取得できる
- Terraform で基盤を再現でき、GitHub Actions からデプロイできる
- CloudWatch でエラーと主要メトリクスを確認できる
