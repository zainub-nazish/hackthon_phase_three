"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  sendMessage as apiSendMessage,
  getConversation,
  getMessages,
} from "@/lib/chat-client";
import { ApiError } from "@/lib/api-client";
import type { Message, ChatState } from "@/types/chat";
import { MAX_MESSAGE_LENGTH } from "@/types/chat";

export function useChat(userId: string) {
  const [state, setState] = useState<ChatState>({
    conversationId: null,
    messages: [],
    isLoading: false,
    error: null,
  });
  const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load conversation history on mount
  useEffect(() => {
    let mounted = true;

    async function loadHistory() {
      try {
        const conv = await getConversation(userId);
        if (!mounted) return;

        if (conv.conversation_id) {
          const history = await getMessages(userId, conv.conversation_id);
          if (!mounted) return;

          setState((prev) => ({
            ...prev,
            conversationId: conv.conversation_id,
            messages: history.messages,
          }));
        }
      } catch {
        // Silently handle — no conversation yet is a valid state
      } finally {
        if (mounted) {
          setIsHistoryLoaded(true);
        }
      }
    }

    loadHistory();

    return () => {
      mounted = false;
    };
  }, [userId]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || state.isLoading) return;

      if (trimmed.length > MAX_MESSAGE_LENGTH) {
        setState((prev) => ({
          ...prev,
          error: `Message too long (${trimmed.length}/${MAX_MESSAGE_LENGTH} characters)`,
        }));
        return;
      }

      // Optimistic: add user message immediately
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: state.conversationId || "",
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
        error: null,
      }));

      try {
        abortControllerRef.current = new AbortController();

        const response = await apiSendMessage(userId, {
          conversation_id: state.conversationId,
          message: trimmed,
        });

        const assistantMessage: Message = {
          id: `msg-${Date.now()}`,
          conversation_id: response.conversation_id,
          role: "assistant",
          content: response.response,
          created_at: new Date().toISOString(),
        };

        setState((prev) => ({
          ...prev,
          conversationId: response.conversation_id,
          messages: [...prev.messages, assistantMessage],
          isLoading: false,
        }));
      } catch (err) {
        // Surface 401 status for auth redirect handling
        const is401 = err instanceof ApiError && err.status === 401;
        const message = is401
          ? "Session expired. Please sign in again."
          : err instanceof Error
            ? err.message
            : "Failed to send message";
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: message,
        }));
      } finally {
        abortControllerRef.current = null;
      }
    },
    [userId, state.conversationId, state.isLoading]
  );

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    isHistoryLoaded,
    sendMessage,
    clearError,
  };
}
