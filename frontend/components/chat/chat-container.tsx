"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { getAuthToken } from "@/lib/auth-client";
import { ChatError } from "./chat-error";
import { ChatWelcome } from "./chat-welcome";
import { useChat } from "@/hooks/use-chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DOMAIN_KEY = process.env.NEXT_PUBLIC_CHATKIT_DOMAIN_KEY || "";

interface ChatContainerProps {
  userId: string;
}

export function ChatContainer({ userId }: ChatContainerProps) {
  const router = useRouter();
  const {
    conversationId,
    messages,
    isLoading,
    error,
    isHistoryLoaded,
    sendMessage,
    clearError,
  } = useChat(userId);

  // Custom fetch that injects auth headers
  const authenticatedFetch = useCallback(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const token = await getAuthToken();
      const headers = new Headers(init?.headers);
      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }
      return fetch(input, { ...init, headers, credentials: "include" });
    },
    []
  );

  const { control } = useChatKit({
    api: {
      url: `${API_URL}/chatkit`,
      domainKey: DOMAIN_KEY,
      fetch: authenticatedFetch,
    },
    theme: {
      colorScheme: "dark",
      radius: "soft",
      density: "normal",
      color: {
        accent: {
          primary: "#2DD4BF",
          level: 1,
        },
      },
    },
    header: {
      enabled: false,
    },
    history: {
      enabled: false,
    },
    startScreen: {
      greeting: "What can I help you with?",
      prompts: [
        {
          label: "Show my tasks",
          prompt: "Show my tasks",
          icon: "check-circle",
        },
        {
          label: "Add a new task",
          prompt: "Add a task to buy groceries",
          icon: "plus",
        },
      ],
    },
    composer: {
      placeholder: "Ask me to manage your tasks...",
    },
    initialThread: conversationId,
    onError: (detail) => {
      console.error("ChatKit error:", detail);
      // Redirect to login on authentication errors
      if (detail && typeof detail === "object" && "status" in detail && (detail as { status: number }).status === 401) {
        router.replace("/login");
      }
    },
  });

  // Show welcome when no conversation and history has been checked
  if (isHistoryLoaded && !conversationId && messages.length === 0) {
    return <ChatWelcome />;
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {error && <ChatError message={error} onRetry={clearError} />}
      <div className="flex-1 overflow-hidden">
        <ChatKit control={control} className="h-full w-full" />
      </div>
    </div>
  );
}
