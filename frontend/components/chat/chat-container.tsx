"use client";

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { ChatError } from "./chat-error";
import { useChat } from "@/hooks/use-chat";

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

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, [isHistoryLoaded]);

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    const msg = input;
    setInput("");
    await sendMessage(msg);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const quickPrompts = [
    { label: "Show my tasks", prompt: "Show my tasks" },
    { label: "Add a task", prompt: "Add a task to buy groceries" },
    { label: "What can you do?", prompt: "What can you do?" },
  ];

  // Welcome screen
  if (isHistoryLoaded && !conversationId && messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col">
        <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <svg
              className="h-8 w-8 text-primary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h2 className="mt-4 text-xl font-semibold text-light">
            AI Task Assistant
          </h2>
          <p className="mt-2 max-w-sm text-sm text-muted">
            Manage your tasks through natural conversation. Try one of the suggestions below.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {quickPrompts.map((qp) => (
              <button
                key={qp.label}
                onClick={() => {
                  setInput(qp.prompt);
                  sendMessage(qp.prompt);
                }}
                className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-light transition-colors hover:border-primary hover:bg-primary/5"
              >
                {qp.label}
              </button>
            ))}
          </div>
        </div>
        {/* Input bar on welcome screen */}
        <div className="border-t border-border p-4">
          <form onSubmit={handleSubmit} className="mx-auto flex max-w-3xl gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me to manage your tasks..."
              rows={1}
              className="flex-1 resize-none rounded-lg border border-border bg-card px-4 py-3 text-sm text-black placeholder-black outline-none transition-colors focus:border-primary"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="rounded-lg bg-primary px-4 py-3 text-sm font-medium text-dark transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {error && <ChatError message={error} onRetry={clearError} />}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-dark"
                    : "bg-card border border-border text-light"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-1.5 rounded-2xl bg-card border border-border px-4 py-3">
                <span className="h-2 w-2 animate-bounce rounded-full bg-primary/60 [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-primary/60 [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-primary/60" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <form onSubmit={handleSubmit} className="mx-auto flex max-w-3xl gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to manage your tasks..."
            rows={1}
            className="flex-1 resize-none rounded-lg border border-border bg-card px-4 py-3 text-sm text-black placeholder-black outline-none transition-colors focus:border-primary"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="rounded-lg bg-primary px-4 py-3 text-sm font-medium text-dark transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              "Send"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
