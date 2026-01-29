/**
 * Better Auth client-side helper.
 *
 * Provides client-side authentication utilities for React components.
 * Build: 2026-01-29-v2
 */

import { createAuthClient } from "better-auth/react";

// Create auth client instance
// Uses NODE_ENV to detect production (Vercel) vs development (local)
const AUTH_URL = process.env.NODE_ENV === "production"
  ? "https://frontend-delta-two-31.vercel.app"
  : "http://localhost:3000";

export const authClient = createAuthClient({
  baseURL: AUTH_URL,
});

// Re-export commonly used methods
export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession,
} = authClient;

/**
 * Get the current session token for API requests.
 *
 * The backend will verify this token by calling Better Auth's session endpoint.
 *
 * @returns Session token string or null if not authenticated
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    const session = await getSession();
    if (session?.data?.session?.token) {
      return session.data.session.token;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Check if user is currently authenticated.
 *
 * @returns true if user has valid session
 */
export async function isAuthenticated(): Promise<boolean> {
  const result = await getSession();
  return result?.data?.user !== null && result?.data?.user !== undefined;
}
