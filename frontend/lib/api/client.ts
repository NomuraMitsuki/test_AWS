"use client";

import { getIdToken } from "@/lib/auth/session";
import type { ApiError } from "./types";

function apiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  return base.replace(/\/$/, "");
}

function toApiError(status: number, body: unknown): ApiError {
  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    const message =
      typeof record.message === "string"
        ? record.message
        : `リクエストに失敗しました（${status}）`;
    return {
      status,
      message,
      code: typeof record.code === "string" ? record.code : undefined,
      request_id:
        typeof record.request_id === "string" ? record.request_id : undefined,
    };
  }
  return {
    status,
    message: `リクエストに失敗しました（${status}）`,
  };
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = await getIdToken();
  if (!token) {
    throw { status: 401, message: "ログインが必要です" } satisfies ApiError;
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const url = `${apiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch {
    throw {
      status: 0,
      message: "ネットワークエラーが発生しました",
    } satisfies ApiError;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let body: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { message: text };
    }
  }

  if (!response.ok) {
    throw toApiError(response.status, body);
  }

  return body as T;
}

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    "message" in error
  );
}

export function errorMessage(error: unknown): string {
  if (isApiError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return "予期しないエラーが発生しました";
}
