# Phase 7 — Next.js フロント + Amplify 設計（W-250）

**日付**: 2026-08-07  
**ステータス**: Approved（apply なしで実装）  
**WBS**: W-250  
**画面正本**: [docs/ui/screens.md](../../ui/screens.md)  
**API 正本**: [docs/api/openapi.yaml](../../api/openapi.yaml)  
**親設計**: [2026-08-05-attendance-aws-design.md](2026-08-05-attendance-aws-design.md) §4.1

## 1. ゴール

`frontend/` に Next.js 14（App Router / TypeScript）で S01〜S12 を実装し、Cognito 認証（Amplify Auth）と API Gateway 呼び出し、Amplify Hosting 用 Terraform、API CORS をリポジトリ上で再現可能にする。検証は lint / `next build` と `terraform validate` まで。**apply は行わない。**

## 2. 非ゴール

- terraform apply / 実 Cognito・Amplify・API の E2E
- W-109（GitHub Secrets / OIDC CI 有効化）
- W-260（frontend / backend Actions の本格完成）。本 Phase では PR 用の最小 `frontend.yml`（`npm ci` / lint / build）を置いてよいが、Amplify デプロイジョブは W-260
- デザインシステム・リッチなビジュアル（学習用のシンプルレイアウト）
- Next.js BFF（Route Handler での API 中継）や静的 export（S3/CloudFront）への変更

## 3. 方針（採用案）

ブラウザが Cognito で認証し、**ID Token** を Bearer として API Gateway に送る（既存シーケンスどおり）。宿主は Amplify Hosting（Gen1 系 `aws_amplify_app` / branch）。

## 4. 構成

```text
frontend/
  app/                      # S01〜S12 ルート（App Router）
  components/               # レイアウト・ナビ・共有 UI
  lib/auth/                 # Amplify Auth 設定・セッション・ロール判定
  lib/api/                  # API Gateway クライアント（Bearer）
  package.json
infra/modules/amplify/      # Amplify App + branch
infra/modules/api/          # CORS（Amplify オリジン）
infra/envs/dev/             # amplify 接続・CORS / 環境変数の配線
```

### 4.1 環境変数（フロント）

| 変数 | 用途 |
|------|------|
| `NEXT_PUBLIC_AWS_REGION` | `ap-northeast-1` |
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | User Pool ID |
| `NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID` | App Client ID（secret なし） |
| `NEXT_PUBLIC_API_BASE_URL` | API Gateway ベース URL |

ローカル用は `.env.example` を置き、実値はコミットしない。

## 5. 認証・画面ガード

| 項目 | 方針 |
|------|------|
| ログイン | email + password。Cognito セルフサインアップなし（既存 User Pool） |
| チャレンジ | `NEW_PASSWORD_REQUIRED` → `/login/new-password`（S02） |
| セッション | Amplify Auth（SRP / リフレッシュ）。未ログインは保護ルートから `/login` へ |
| UI ロール | JWT の Cognito groups（`employee` / `manager` / `admin`）でナビ表示と画面入場を制御 |
| API 認可 | 最終判定は従来どおり Lambda / DB。フロントのガードは UX 用 |

ロール外（S07 / S10 / S11）はナビ非表示に加え、直接 URL でも拒否案内を表示する。

## 6. 画面（S01〜S12）

[screens.md](../../ui/screens.md) のパス・ロールを正とする。

| ID | パス | 主な API |
|----|------|----------|
| S01 | `/login` | Cognito のみ |
| S02 | `/login/new-password` | Cognito のみ |
| S03 | `/` | 当日打刻状態。manager/admin は承認待ち件数 |
| S04 | `/attendance` | 出勤／退勤 |
| S05 | `/attendance/history` | `GET /attendance/records?scope=self` |
| S06 | `/attendance/summary` | `GET /attendance/summary` |
| S07 | `/attendance/team` | `GET /attendance/records?scope=team\|all` |
| S08 | `/leave` | `GET /leave-requests?scope=self` |
| S09 | `/leave/new` | `POST /leave-requests` |
| S10 | `/leave/approvals` | pending 一覧＋承認／却下 |
| S11 | `/admin/users` | users 一覧・招待・更新 |
| S12 | `/exports` | `POST /exports/attendance` → 署名付き URL |

### 6.1 UI 方針

- ヘッダーナビ ＋ メインのシンプルレイアウト（日本語ラベル）
- 打刻ボタンは状態に応じて活性化／非活性化
- エクスポート成功時は署名付き URL を新しいタブまたはダウンロードで開き、画面に長時間表示しない
- API エラーは日本語メッセージで表示

## 7. API クライアント

- `fetch` ラッパが `Authorization: Bearer <idToken>` を付与
- ベース URL は `NEXT_PUBLIC_API_BASE_URL`
- 4xx/5xx は呼び出し側で扱いやすい形に正規化（メッセージ表示用）

## 8. インフラ

### 8.1 Amplify モジュール

- `aws_amplify_app` + `aws_amplify_branch`（例: `main`）
- アプリルート: `frontend`
- フレームワーク: Next.js（SSR 対応 Hosting）
- 環境変数は Amplify 側にも同名で渡せるよう変数化
- GitHub リポジトリ接続用トークン等は Terraform 変数（sensitive）。apply までは未設定でも `validate` 可能な形にする（ダミー／optional の扱いは実装計画で固定）

### 8.2 API CORS

- Phase 2 で未設定だった CORS を、Amplify オリジン（変数、例: `https://main.<appId>.amplifyapp.com` およびローカル `http://localhost:3000`）に限定して許可
- メソッド・ヘッダはフロントの `fetch` に必要な最小（`Authorization` / `Content-Type` 等）
- credentials cookie は使わない（Bearer のみ）

### 8.3 Cognito

既存 App Client（secret なし、USER_SRP / PASSWORD）をそのまま利用。本 Phase でクライアント設定を変える必要があれば最小差分のみ。

## 9. 検証

- `frontend`: `npm ci` / lint / `next build`（環境変数はビルド用ダミー可）
- `infra/envs/dev`: `terraform fmt` / `validate`（apply なし）
- 画面の E2E（実 Cognito）は対象外。必要なら Auth / API クライアントの単体テストを最小限

## 10. 完了後の位置づけ

- WBS W-250 を完了（親がステータス更新）
- 次: W-260（CI 完成）またはユーザー方針に従い W-109（API・フロント完了後の再 apply / Secrets）
