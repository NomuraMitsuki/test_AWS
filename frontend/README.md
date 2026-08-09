# フロントエンド（Next.js 14）

## デモモード（レビュー用）

Cognito / API なしで S01〜S12 の画面確認ができます。**本番 Amplify では `NEXT_PUBLIC_DEMO_MODE` を設定しないでください。**

```bash
cd frontend
npm ci          # 初回のみ
npm run dev:demo
```

ブラウザで `http://localhost:3000` を開き、ロール（一般社員 / 上長 / 管理者）を選んでログインします。

## 通常起動（実 Cognito）

`.env.example` を `.env.local` にコピーし、User Pool / Client / API URL を設定して `npm run dev`。
