"use client";

import { Button } from "@/components/ui/button";

interface ChatErrorProps {
  message: string;
  onRetry: () => void;
}

export function ChatError({ message, onRetry }: ChatErrorProps) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-danger/20 bg-danger/5 p-4">
      <svg
        className="h-5 w-5 shrink-0 text-danger"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>
      <div className="flex-1">
        <p className="text-sm text-light">{message}</p>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="mt-2 text-danger hover:text-danger"
        >
          Try again
        </Button>
      </div>
    </div>
  );
}
