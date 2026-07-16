"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isStandalonePage = pathname === "/" || pathname === "/login" || pathname === "/signup";

  return (
    <div className="flex min-h-screen w-full relative bg-background text-on-surface font-body-md overflow-x-hidden">
      {!isStandalonePage && <Sidebar />}
      <div className="flex-1 w-full min-w-0 relative flex flex-col">
        {children}
      </div>
    </div>
  );
}
