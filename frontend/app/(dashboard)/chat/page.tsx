"use client";

import { useAuth } from "@/hooks/use-auth";
import { Spinner } from "@/components/ui/spinner";
import { ChatContainer } from "@/components/chat/chat-container";

export default function ChatPage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-5rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col">
      <ChatContainer userId={user.id} />
    </div>
  );
}
