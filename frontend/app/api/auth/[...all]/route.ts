/**
 * Better Auth API route handler.
 *
 * This catch-all route handles all Better Auth API requests
 * including signin, signup, signout, and session management.
 */

import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

// Use Node.js runtime for database compatibility
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Export handlers for all HTTP methods
export const { GET, POST } = toNextJsHandler(auth);
