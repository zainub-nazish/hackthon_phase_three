"use client";

import { usePathname } from "next/navigation";
import { AuthGuard } from "@/components/auth/auth-guard";
import { Header } from "@/components/layout/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isChat = pathname === "/chat";

  return (
    <AuthGuard>
      <div className="min-h-screen bg-dark">
        <Header />
        <main
          className={
            isChat
              ? ""
              : "mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8"
          }
        >
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}
