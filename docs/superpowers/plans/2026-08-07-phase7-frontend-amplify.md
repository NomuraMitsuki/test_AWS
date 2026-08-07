# Phase 7 Frontend + Amplify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本リポジトリでは親が `implementation-worker` に本計画全体を委譲してもよい。

**Goal:** S01〜S12 の Next.js 14 フロント、Cognito（Amplify Auth）、API Gateway クライアント、Amplify Hosting Terraform、API CORS を実装し、lint / `next build` / `terraform validate` を通す（apply なし）。

**Architecture:** ブラウザが Amplify Auth で Cognito 認証し ID Token を Bearer で API Gateway に送る。画面は App Router。ダッシュボード専用 API は作らず既存エンドポイントを合成。`infra/modules/amplify` を新設し、`api` に CORS を追加。

**Tech Stack:** Next.js 14 (App Router), TypeScript, `aws-amplify` v6 Auth, Terraform, GitHub Actions（PR 用最小 frontend.yml のみ）

## Global Constraints

- apply しない。W-109 に触れない。`docs/wbs.md` のステータスは触らない（親が更新）
- スペック: [docs/superpowers/specs/2026-08-07-phase7-frontend-amplify-design.md](../specs/2026-08-07-phase7-frontend-amplify-design.md)
- 画面正本: [docs/ui/screens.md](../../ui/screens.md) / API: [docs/api/openapi.yaml](../../api/openapi.yaml)
- UI は日本語・機能優先のシンプルレイアウト（ヘッダーナビ＋メイン）
- 秘密情報をコミットしない。`.env*.local` は gitignore
- PR 操作しない。完了後 push（ブランチ `cursor/w250-frontend-a099`）

## File structure（予定）

```text
frontend/
  package.json
  tsconfig.json
  next.config.mjs
  .env.example
  app/layout.tsx
  app/globals.css
  app/login/page.tsx
  app/login/new-password/page.tsx
  app/(app)/layout.tsx          # 認証必須レイアウト
  app/(app)/page.tsx            # S03
  app/(app)/attendance/page.tsx
  app/(app)/attendance/history/page.tsx
  app/(app)/attendance/summary/page.tsx
  app/(app)/attendance/team/page.tsx
  app/(app)/leave/page.tsx
  app/(app)/leave/new/page.tsx
  app/(app)/leave/approvals/page.tsx
  app/(app)/admin/users/page.tsx
  app/(app)/exports/page.tsx
  components/AppHeader.tsx
  components/RequireRole.tsx
  lib/auth/amplify.ts
  lib/auth/session.ts           # getIdToken, getGroups, Role
  lib/api/client.ts
  lib/api/types.ts
.gitignore                      # frontend node_modules / .next 等（未記載なら追加）
infra/modules/amplify/{main,variables,outputs}.tf
infra/modules/api/              # CORS
infra/envs/dev/{main,variables,outputs,terraform.tfvars}
.github/workflows/frontend.yml  # npm ci / lint / build のみ
```

---

### Task 1: Next.js スキャフォールド + Auth + API クライアント

**Files:**
- Create: 上記 `frontend/` の設定ファイル、`lib/auth/*`、`lib/api/*`、`app/layout.tsx`、`app/globals.css`、`app/login/*`、`app/(app)/layout.tsx`、`components/*`
- Create: `frontend/.env.example`
- Modify: ルート `.gitignore`（必要なら）

**Behavior:**
- `configureAmplify()` が env から User Pool / Client / Region を読む
- `getIdToken(): Promise<string | null>` / `getGroups(): Promise<string[]>` / `hasRole(role)`
- `apiFetch<T>(path, init)` が Bearer 付与。401/403/4xx/5xx を `{ status, message }` 形に正規化
- 未ログインで `(app)` 配下へ来たら `/login` へ
- ビルド用ダミー env で `next build` が通ること

**Env names（固定）:**
- `NEXT_PUBLIC_AWS_REGION`
- `NEXT_PUBLIC_COGNITO_USER_POOL_ID`
- `NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID`
- `NEXT_PUBLIC_API_BASE_URL`

- [ ] `npm ci` / lint / `next build`（ダミー env）
- [ ] Commit: `feat(frontend): scaffold Next.js auth and API client (W-250)`

---

### Task 2: 勤怠画面（S03 一部・S04〜S07）

**Files:**
- Create/Modify: `app/(app)/page.tsx`（打刻状態部分）, `attendance/*`

**API:**
- S04: `POST /attendance/clock-in` | `POST /attendance/clock-out` + 当日状態表示
- S05: `GET /attendance/records?scope=self`
- S06: `GET /attendance/summary`（任意 query `user_id`, `year_month`）
- S07: `GET /attendance/records?scope=team|all`（manager/admin）。`RequireRole`。行から summary へ `user_id` 付き遷移

- [ ] lint / build
- [ ] Commit: `feat(frontend): add attendance screens (W-250)`

---

### Task 3: 休暇・ユーザー・エクスポート・ダッシュボード完成（S03・S08〜S12）

**Files:**
- Create: `leave/*`, `admin/users/page.tsx`, `exports/page.tsx`
- Modify: `app/(app)/page.tsx` — manager/admin は `GET /leave-requests?scope=team|all&status=pending` 件数

**API:**
- S08/S09: list + `POST /leave-requests`
- S10: pending + `POST .../approve|reject`（manager/admin）
- S11: `GET/POST /users`, `PATCH /users/{id}`（admin）
- S12: `POST /exports/attendance` body `{ from_date, to_date, scope }` → `download_url` を `window.open` またはダウンロード。URL を画面に残さない

- [ ] lint / build（全画面ルートがビルドに含まれること）
- [ ] Commit: `feat(frontend): add leave users exports dashboard (W-250)`

---

### Task 4: Amplify モジュール + API CORS + envs 配線

**Files:**
- Create: `infra/modules/amplify/{main.tf,variables.tf,outputs.tf}`
- Modify: `infra/modules/api/*` — HTTP API CORS
- Modify: `infra/envs/dev/{main.tf,variables.tf,outputs.tf,terraform.tfvars}`

**Amplify:**
- `aws_amplify_app` + `aws_amplify_branch`（例: `main`）
- `platform` / build spec で Next.js、`app_root = "frontend"`
- 環境変数に Cognito / API URL を渡せる variables
- `access_token`（GitHub）は `sensitive` optional。未設定でも `terraform validate` 可能にする（lifecycle / 条件付きリソース、または token 変数を空文字デフォルト＋ドキュメントで apply 前必須と明記。**validate が通る形を選ぶ**）

**CORS:**
- allow origins: Amplify デフォルト URL（変数）+ `cors_allow_localhost=true` のとき `http://localhost:3000`
- allow headers: `authorization`, `content-type`
- allow methods: GET, POST, PATCH, OPTIONS（必要なもの）
- allow credentials: false

- [ ] `terraform fmt` / `terraform init -backend=false` / `terraform validate` in `infra/envs/dev`
- [ ] Commit: `feat(infra): add Amplify module and API CORS (W-250)`

---

### Task 5: 最小 frontend CI + docs 同期

**Files:**
- Create: `.github/workflows/frontend.yml` — PR / push on `frontend/**` で `npm ci` / lint / `next build`（ダミー env）。Amplify deploy ジョブは作らない（W-260）
- Modify: `README.md`（Phase 7 計画リンク）, `docs/infra/terraform-design.md`（実装と食い違う点のみ）, `infra/README.md`, `docs/handoff.md`（実装完了後の事実。**次作業は W-260 / W-109 方針**）。`docs/wbs.md` は触らない

- [ ] Commit: `docs: sync Phase 7 frontend plan and handoff (W-250)`
- [ ] Push `cursor/w250-frontend-a099`

---

## 親が行うこと

- 設計レビュー（実装後の差分）→ PR 更新、`docs/wbs.md` で W-250 完了
- apply / W-109 はユーザー指示があるまでしない
