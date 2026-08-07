"use client";

import { fetchAuthSession, getCurrentUser, signOut } from "aws-amplify/auth";
import { configureAmplify } from "./amplify";

export type Role = "employee" | "manager" | "admin";

const ROLES: Role[] = ["employee", "manager", "admin"];

function asRole(value: string): Role | null {
  return ROLES.includes(value as Role) ? (value as Role) : null;
}

export async function getIdToken(): Promise<string | null> {
  configureAmplify();
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() ?? null;
  } catch {
    return null;
  }
}

export async function getGroups(): Promise<string[]> {
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
  configureAmplify();
  try {
    await getCurrentUser();
    return true;
  } catch {
    return false;
  }
}

export async function logout(): Promise<void> {
  configureAmplify();
  await signOut();
}
