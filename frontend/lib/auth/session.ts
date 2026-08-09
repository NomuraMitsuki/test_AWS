"use client";

import { fetchAuthSession, getCurrentUser, signOut } from "aws-amplify/auth";
import { isDemoMode } from "@/lib/demo/mode";
import {
  clearDemoSession,
  getDemoSession,
} from "@/lib/demo/session";
import { configureAmplify } from "./amplify";

export type Role = "employee" | "manager" | "admin";

const ROLES: Role[] = ["employee", "manager", "admin"];

function asRole(value: string): Role | null {
  return ROLES.includes(value as Role) ? (value as Role) : null;
}

export async function getIdToken(): Promise<string | null> {
  if (isDemoMode()) {
    return getDemoSession() ? "demo-id-token" : null;
  }
  configureAmplify();
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() ?? null;
  } catch {
    return null;
  }
}

export async function getGroups(): Promise<string[]> {
  if (isDemoMode()) {
    const demo = getDemoSession();
    return demo ? [demo.role] : [];
  }
  configureAmplify();
  try {
    const session = await fetchAuthSession();
    const groups = session.tokens?.idToken?.payload["cognito:groups"];
    if (Array.isArray(groups)) {
      return groups.map(String);
    }
    return [];
  } catch {
    return [];
  }
}

export async function getRoles(): Promise<Role[]> {
  const groups = await getGroups();
  return groups.map(asRole).filter((r): r is Role => r !== null);
}

export async function hasRole(role: Role): Promise<boolean> {
  const roles = await getRoles();
  return roles.includes(role);
}

export async function isAuthenticated(): Promise<boolean> {
  if (isDemoMode()) {
    return getDemoSession() !== null;
  }
  configureAmplify();
  try {
    await getCurrentUser();
    return true;
  } catch {
    return false;
  }
}

export async function logout(): Promise<void> {
  if (isDemoMode()) {
    clearDemoSession();
    return;
  }
  configureAmplify();
  await signOut();
}
