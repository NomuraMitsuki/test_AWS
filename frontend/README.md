# フロントエンド（Next.js 14）

## デモモード（レビュー用）

Cognito / API なしで S01〜S12 の画面確認ができます。**本番 Amplify では `NEXT_PUBLIC_DEMO_MODE` を設定しないでください。**

```bash
cd frontend
npm ci
NEXT_PUBLIC_DEMO_MODE=true \
NEXT_PUBLIC_AWS_REGION=ap-northeast-1 \
NEXT_PUBLIC_COGNITO_USER_POOL_ID=ap-northeast-1_dummy \
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=dummyclient \
NEXT_PUBLIC_API_BASE_URL=https://example.execute-api.ap-northeast-1.amazonaws.com \
npm run dev -- -H 0.0.0.0 -p 3000
```

ブラウザで `http://localhost:3000` を開き、ロール（一般社員 / 上長 / 管理者）を選んでログインします。

## 通常起動（実 Cognito）

`.env.example` を `.env.local` にコピーし、User Pool / Client / API URL を設定して `npm run dev`。
