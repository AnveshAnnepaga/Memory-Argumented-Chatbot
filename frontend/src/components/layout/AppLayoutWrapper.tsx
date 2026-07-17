"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isStandalonePage = pathname === "/" || pathname === "/login" || pathname === "/signup" || pathname === "/auth";

  if (isStandalonePage) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-on-surface font-body-md">
      {/* Fixed sidebar */}
      <Sidebar />

      {/* Main column: Navbar (sticky) + scrollable page content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto custom-scrollbar">
          {children}
        </main>
      </div>
    </div>
  );
}
