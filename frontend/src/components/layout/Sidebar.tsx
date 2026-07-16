"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  name: string;
  href: string;
  icon: string;
}

const navItems: NavItem[] = [
  { name: "Overview", href: "/", icon: "dashboard" },
  { name: "Chat Studio", href: "/chat", icon: "forum" },
  { name: "Knowledge", href: "/knowledge", icon: "auto_stories" },
  { name: "Memory", href: "/memory", icon: "memory" },
  { name: "Graph", href: "/graph", icon: "hub" },
  { name: "Evaluation", href: "/evaluation", icon: "analytics" },
  { name: "History", href: "/history", icon: "history" },
];

const bottomNavItems: NavItem[] = [
  { name: "About", href: "/about", icon: "info" },
  { name: "Settings", href: "/settings", icon: "settings" },
  { name: "Admin", href: "/admin", icon: "admin_panel_settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="fixed left-0 top-0 bottom-0 w-64 z-40 flex flex-col p-md gap-sm bg-surface-container-low border-r border-outline-variant/20">
      <div className="flex items-center gap-sm mb-lg px-xs">
        <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center">
          <span className="material-symbols-outlined text-on-primary-container text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            auto_awesome
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-headline-md font-headline-md font-black text-primary">Antigravity AI</span>
          <span className="text-label-md font-label-md text-on-surface-variant">Enterprise Architect</span>
        </div>
      </div>

      <div className="flex flex-col gap-xs flex-grow overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={
                isActive
                  ? "flex items-center gap-md p-sm bg-primary-container text-on-primary-container rounded-lg font-semibold scale-[0.98] transition-transform shadow-md shadow-primary-container/10"
                  : "flex items-center gap-md p-sm text-on-surface-variant hover:bg-surface-variant/50 rounded-lg transition-colors"
              }
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="text-label-md font-label-md">{item.name}</span>
            </Link>
          );
        })}
      </div>

      <div className="mt-auto pt-lg border-t border-outline-variant/20 flex flex-col gap-xs">
        {bottomNavItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={
                isActive
                  ? "flex items-center gap-md p-sm bg-primary-container text-on-primary-container rounded-lg font-semibold scale-[0.98] transition-transform shadow-md shadow-primary-container/10"
                  : "flex items-center gap-md p-sm text-on-surface-variant hover:bg-surface-variant/50 rounded-lg transition-colors"
              }
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="text-label-md font-label-md">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
