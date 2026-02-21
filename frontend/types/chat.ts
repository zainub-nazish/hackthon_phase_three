/**
 * Chat UI TypeScript Types
 *
 * Contract types for the Chat feature.
 * These types mirror the backend Chat API schemas.
 */

// =============================================================================
// Chat Message Types
// =============================================================================

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// Chat API Request/Response Types
// =============================================================================

export interface ChatRequest {
  conversation_id: string | null;
  message: string;
}

export interface ToolCall {
  tool_name: string;
  parameters: string;
  result: string;
  status: string;
}

export interface ChatResponse {
  conversation_id: string;
  response: string;
  tool_calls: ToolCall[];
}

export interface ConversationResponse {
  conversation_id: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface MessagesResponse {
  conversation_id: string;
  messages: Message[];
}

// =============================================================================
// Chat UI State
// =============================================================================

export interface ChatState {
  conversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export const MAX_MESSAGE_LENGTH = 1000;
