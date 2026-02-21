/**
 * Better Auth client-side helper.
 *
 * Provides client-side authentication utilities for React components.
 */

import { createAuthClient } from "better-auth/react";

// Determine the base URL for auth API calls
function getBaseURL(): string {
  // In browser, use current origin
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  // On server, use environment variable or fallback
  return process.env.NEXT_PUBLIC_APP_URL || "https://frontend-delta-two-31.vercel.app";
}

// Create auth client with explicit baseURL and fetch options
export const authClient = createAuthClient({
  baseURL: getBaseURL(),
  fetchOptions: {
    credentials: "include", // Required for cookies to work cross-origin
  },
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
    console.warn("[Auth] No session token found in session data:", JSON.stringify(session?.data, null, 2));
    return null;
  } catch (err) {
    console.error("[Auth] getAuthToken error:", err);
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
