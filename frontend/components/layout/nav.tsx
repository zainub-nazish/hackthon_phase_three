"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavProps {
  className?: string;
}

export function MobileNav({ className }: NavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { href: "/tasks", label: "Tasks" },
    { href: "/chat", label: "Chat" },
  ];

  return (
    <div className={cn("md:hidden", className)}>
      {/* Mobile menu button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center justify-center rounded-md p-2 text-muted hover:bg-white/5 hover:text-light focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-surface transition-colors"
        aria-expanded={isOpen}
        aria-controls="mobile-menu"
        aria-label={isOpen ? "Close menu" : "Open menu"}
      >
        <span className="sr-only">{isOpen ? "Close menu" : "Open menu"}</span>
        {isOpen ? (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        ) : (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        )}
      </button>

      {/* Mobile menu panel */}
      {isOpen && (
        <div
          id="mobile-menu"
          className="absolute left-0 right-0 top-16 z-50 border-b border-white/10 bg-surface shadow-lg"
        >
          <nav className="space-y-1 px-4 py-3" aria-label="Mobile navigation">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    "block rounded-md px-3 py-3 text-base font-medium transition-colors min-h-[44px] flex items-center",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted hover:bg-white/5 hover:text-light"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </div>
  );
}

export function DesktopNav({ className }: NavProps) {
  const pathname = usePathname();

  const navItems = [
    { href: "/tasks", label: "Tasks" },
    { href: "/chat", label: "Chat" },
  ];

  return (
    <nav
      className={cn("hidden md:flex items-center gap-1", className)}
      aria-label="Main navigation"
    >
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.label}
            href={item.href}
            className={cn(
              "px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "text-primary border-b-2 border-primary"
                : "text-muted hover:text-light"
            )}
            aria-current={isActive ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
