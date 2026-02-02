/**
 * Better Auth client-side helper.
 *
 * Provides client-side authentication utilities for React components.
 * Build: 2026-02-02-v7 - Fixed URL detection for Vercel
 */

import { createAuthClient } from "better-auth/react";

// Create auth client - baseURL will be automatically detected by Better Auth
// When baseURL is not provided, Better Auth uses the current origin
export const authClient = createAuthClient({
  // Don't set baseURL - let Better Auth auto-detect from current origin
  // This ensures it works correctly on both localhost and Vercel
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
