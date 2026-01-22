/**
 * Better Auth client-side helper.
 *
 * Provides client-side authentication utilities for React components.
 */

import { createAuthClient } from "better-auth/react";

// Create auth client instance
// Better Auth will automatically use the current origin for API calls
export const authClient = createAuthClient({
  // baseURL is optional - Better Auth uses current origin by default
  baseURL: process.env.NEXT_PUBLIC_APP_URL || undefined,
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
