"use client";

export function ChatWelcome() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
      <svg
        className="h-16 w-16 text-primary/50"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      <h2 className="mt-4 text-xl font-semibold text-light">
        Chat with your AI assistant
      </h2>
      <p className="mt-2 max-w-sm text-sm text-muted">
        Ask me to manage your tasks. Try something like &quot;Add a task to buy
        groceries&quot; or &quot;Show my tasks&quot;.
      </p>
    </div>
  );
}
