import api from "./api";
import type {
  AuthUser,
  CreateUserPayload,
  TokenResponse,
  UserRole,
} from "@/types/auth";

const TOKEN_KEY = "access_token";
const USER_KEY = "auth_user";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}

export function isAdmin(): boolean {
  return getStoredUser()?.role === "admin";
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", email.trim());
  body.set("password", password);

  const { data } = await api.post<TokenResponse>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  return data;
}

export async function getMe(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/auth/me");
  localStorage.setItem(USER_KEY, JSON.stringify(data));
  return data;
}

/** Création d'utilisateur — réservé admin (POST /auth/users) */
export async function createUser(
  payload: CreateUserPayload
): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>("/auth/users", payload);
  return data;
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export type { UserRole };
