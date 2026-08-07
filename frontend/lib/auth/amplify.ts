"use client";

import { Amplify } from "aws-amplify";

let configured = false;

export function configureAmplify(): void {
  if (configured) return;

  const region = process.env.NEXT_PUBLIC_AWS_REGION;
  const userPoolId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID;
  const userPoolClientId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID;

  if (!region || !userPoolId || !userPoolClientId) {
    console.warn(
      "Amplify Auth: Cognito 環境変数が未設定です（NEXT_PUBLIC_AWS_REGION / USER_POOL_ID / CLIENT_ID）",
    );
  }

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: userPoolId ?? "",
        userPoolClientId: userPoolClientId ?? "",
      },
    },
  });

  configured = true;
}
