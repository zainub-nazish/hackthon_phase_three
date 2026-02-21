/**
 * API client with automatic JWT token attachment.
 *
 * All requests to the backend API automatically include the
 * JWT token in the Authorization header.
 */

import { getAuthToken } from "./auth-client";

// NEXT_PUBLIC_API_URL is locked to phase-three in vercel.json env (overrides Vercel project settings).
// Falls back to relative URL so Next.js/Vercel rewrites handle routing.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * API client error with status code.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Make an authenticated API request.
 *
 * Automatically attaches JWT token from Better Auth session
 * to the Authorization header.
 *
 * @param endpoint - API endpoint path (e.g., "/api/v1/auth/session")
 * @param options - Fetch options (method, body, etc.)
 * @returns Parsed JSON response
 * @throws ApiError if request fails
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Attach Bearer token if available
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    const url = `${API_URL}${endpoint}`;
    console.log(`[API] ${options.method || "GET"} ${url}`, token ? "(token attached)" : "(no token)");
    response = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Include cookies for CORS
    });
  } catch (fetchError) {
    throw new ApiError("Network error: Unable to connect to server", 0, fetchError);
  }

  // Handle error responses
  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }

    const message =
      typeof errorData === "object" && errorData !== null && "detail" in errorData
        ? String((errorData as { detail: unknown }).detail)
        : `API error: ${response.status}`;

    throw new ApiError(message, response.status, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// Convenience methods
// =============================================================================

/**
 * GET request to API.
 */
export function get<T>(endpoint: string): Promise<T> {
  return apiClient<T>(endpoint, { method: "GET" });
}

/**
 * POST request to API.
 */
export function post<T>(endpoint: string, data?: unknown): Promise<T> {
  return apiClient<T>(endpoint, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * PATCH request to API.
 */
export function patch<T>(endpoint: string, data?: unknown): Promise<T> {
  return apiClient<T>(endpoint, {
    method: "PATCH",
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * DELETE request to API.
 */
export function del<T>(endpoint: string): Promise<T> {
  return apiClient<T>(endpoint, { method: "DELETE" });
}
