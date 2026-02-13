/**
 * Chat API client helper functions.
 *
 * Uses the existing apiClient from api-client.ts for authenticated requests.
 */

import { get, post } from "./api-client";
import type {
  ChatRequest,
  ChatResponse,
  ConversationResponse,
  MessagesResponse,
} from "@/types/chat";

/**
 * Send a chat message and receive an AI response.
 */
export async function sendMessage(
  userId: string,
  request: ChatRequest
): Promise<ChatResponse> {
  return post<ChatResponse>(`/api/v1/users/${userId}/chat`, request);
}

/**
 * Get the user's most recent conversation.
 */
export async function getConversation(
  userId: string
): Promise<ConversationResponse> {
  return get<ConversationResponse>(`/api/v1/users/${userId}/conversations`);
}

/**
 * Load conversation message history.
 */
export async function getMessages(
  userId: string,
  conversationId: string
): Promise<MessagesResponse> {
  return get<MessagesResponse>(
    `/api/v1/users/${userId}/conversations/${conversationId}/messages`
  );
}
