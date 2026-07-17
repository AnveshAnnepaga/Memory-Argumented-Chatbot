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
  { name: "Home", href: "/", icon: "dashboard" },
  { name: "Chat", href: "/chat", icon: "forum" },
  { name: "Knowledge", href: "/knowledge", icon: "auto_stories" },
  { name: "Memory", href: "/memory", icon: "memory" },
  { name: "Graph", href: "/graph", icon: "hub" },
  { name: "History", href: "/history", icon: "history" },
];

const bottomNavItems: NavItem[] = [
  { name: "Settings", href: "/settings", icon: "settings" },
  { name: "Profile", href: "/profile", icon: "account_circle" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="w-64 flex-shrink-0 h-full flex flex-col py-4 px-3 gap-1 bg-surface-container-low border-r border-outline-variant/20 overflow-y-auto custom-scrollbar">
      {/* Brand */}
      <div className="flex items-center gap-3 mb-4 px-2 py-2">
        <div className="w-9 h-9 rounded-xl bg-primary-container flex items-center justify-center shadow-lg shadow-primary-container/20 flex-shrink-0 overflow-hidden">
          <img
            src="/vyron-logo.png"
            alt="Vyron"
            className="w-6 h-6 object-contain"
          />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-[15px] font-black text-primary tracking-tight leading-tight truncate">
            Vyron
          </span>
          <span className="text-[11px] font-mono text-on-surface-variant uppercase tracking-wider">
            AI
          </span>
        </div>
      </div>

      {/* Section label */}
      <p className="text-[10px] font-mono font-bold text-on-surface-variant/50 uppercase tracking-widest px-3 mb-1">
        Navigation
      </p>

      {/* Main nav items */}
      <div className="flex flex-col gap-0.5 flex-grow">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={
                isActive
                  ? "flex items-center gap-3 px-3 py-2.5 bg-primary-container text-on-primary-container rounded-xl font-semibold transition-all shadow-sm shadow-primary-container/20"
                  : "flex items-center gap-3 px-3 py-2.5 text-on-surface-variant hover:bg-surface-container hover:text-on-surface rounded-xl transition-colors"
              }
            >
              <span
                className="material-symbols-outlined text-[20px] flex-shrink-0"
                style={
                  isActive ? { fontVariationSettings: "'FILL' 1" } : undefined
                }
              >
                {item.icon}
              </span>
              <span className="text-[13px] font-medium">{item.name}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-on-primary-container/60 flex-shrink-0" />
              )}
            </Link>
          );
        })}
      </div>

      {/* Bottom nav items */}
      <div className="mt-2 pt-3 border-t border-outline-variant/20 flex flex-col gap-0.5">
        <p className="text-[10px] font-mono font-bold text-on-surface-variant/50 uppercase tracking-widest px-3 mb-1">
          Account
        </p>
        {bottomNavItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={
                isActive
                  ? "flex items-center gap-3 px-3 py-2.5 bg-primary-container text-on-primary-container rounded-xl font-semibold transition-all shadow-sm shadow-primary-container/20"
                  : "flex items-center gap-3 px-3 py-2.5 text-on-surface-variant hover:bg-surface-container hover:text-on-surface rounded-xl transition-colors"
              }
            >
              <span
                className="material-symbols-outlined text-[20px] flex-shrink-0"
                style={
                  isActive ? { fontVariationSettings: "'FILL' 1" } : undefined
                }
              >
                {item.icon}
              </span>
              <span className="text-[13px] font-medium">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
