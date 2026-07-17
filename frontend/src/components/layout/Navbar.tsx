'use client';

import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import { ShieldCheck, Bell, Radio } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Platform Overview & Architecture', subtitle: 'Real-Time 6-Layer Intelligence Orchestration Engine' },
  '/chat': { title: 'Neural Chat & Reasoning Studio', subtitle: 'Live SSE Streaming, RAG Citations & Graph Traversal Timeline' },
  '/history': { title: 'Conversation History & Archive', subtitle: 'Manage, Pin, Search, and Export Multi-Turn Sessions' },
  '/memory': { title: 'Long-Term Memory Dashboard', subtitle: 'User Profile, Semantic Facts, Episodes & Forgetting Curves' },
  '/knowledge': { title: 'Knowledge Base & Ingestion Registry', subtitle: 'Pinecone Vector Indexing (1024-d), Chunks & Source Management' },
  '/graph': { title: 'Neo4j GraphRAG Visualizer', subtitle: 'Interactive Force-Directed Knowledge Graph Traversal & Entity Explorer' },
  '/evaluation': { title: 'Evaluation & Observability Platform', subtitle: 'Real-Time Latency Breakdown, RAG/Graph Accuracy & Hallucination Scoring' },
  '/admin': { title: 'Admin Control Center', subtitle: 'Trigger Re-Indexing, Graph Synchronization, Memory Cleanup & Feature Flags' },
  '/settings': { title: 'System Configuration & Cost Parameters', subtitle: 'Configure LLM Token Rates, API Endpoints & System Limits' },
  '/about': { title: 'About & Portfolio Showcase', subtitle: 'Designed and Engineered by Anvesh Mishra' },
  '/profile': { title: 'User Profile', subtitle: 'Manage your account and preferences' },
};

export function Navbar() {
  const pathname = usePathname();
  const { user, authUser, isAuthenticated, systemHealth, notifications, setAuthModalOpen } = useAppStore();
  const [showNotifications, setShowNotifications] = useState(false);

  const current = PAGE_TITLES[pathname] || {
    title: 'Vyron AI Platform',
    subtitle: 'Production Intelligence Studio',
  };

  const displayName = authUser?.full_name || user?.name || 'User';
  const displayEmail = authUser?.email || user?.email || '';
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-outline-variant/20 glass-surface backdrop-blur-xl flex-shrink-0">
      {/* Page Title */}
      <div className="min-w-0 flex-1 pr-4">
        <h1 className="text-[15px] font-semibold tracking-wide text-on-surface flex items-center gap-2.5">
          <span className="truncate">{current.title}</span>
          <span className="hidden sm:inline-flex items-center whitespace-nowrap px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-primary/10 text-primary border border-primary/20 flex-shrink-0">
            VYRON AI
          </span>
        </h1>
        <p className="text-[12px] text-on-surface-variant hidden sm:block truncate mt-0.5">
          {current.subtitle}
        </p>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 flex-shrink-0 ml-4">
        {/* Live API status */}
        <div className="hidden md:flex items-center px-3 py-1.5 rounded-full bg-surface-container-high border border-outline-variant/20 gap-2">
          <Radio className="w-3.5 h-3.5 text-primary animate-pulse" />
          <span className="text-[11px] font-mono text-on-surface-variant">
            API: <span className="text-tertiary font-bold">ONLINE</span>
          </span>
        </div>

        {/* System Health Badge */}
        <div className={`flex items-center px-3 py-1.5 rounded-full border text-xs font-mono font-semibold gap-1.5 ${
          systemHealth === 'HEALTHY'
            ? 'bg-tertiary/10 border-tertiary/30 text-tertiary'
            : systemHealth === 'WARNING'
            ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
            : 'bg-error/10 border-error/30 text-error'
        }`}>
          <ShieldCheck className="w-4 h-4" />
          <span>{systemHealth}</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications((v) => !v)}
            className="p-2 rounded-xl bg-surface-container border border-outline-variant/20 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors relative"
            title="System Notifications"
          >
            <Bell className="w-4 h-4" />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-secondary text-[10px] font-bold text-on-secondary flex items-center justify-center animate-bounce">
                {notifications.length}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-80 glass-surface rounded-xl border border-outline-variant/20 shadow-2xl z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-outline-variant/20">
                <span className="text-label-md font-bold text-on-surface">Notifications</span>
              </div>
              {notifications.length === 0 ? (
                <div className="px-4 py-6 text-center text-body-sm text-on-surface-variant">No notifications</div>
              ) : (
                <div className="max-h-64 overflow-y-auto custom-scrollbar">
                  {notifications.map((n) => (
                    <div key={n.id} className="px-4 py-3 border-b border-outline-variant/10 hover:bg-surface-container-high transition-colors">
                      <p className="text-body-sm font-semibold text-on-surface">{n.title}</p>
                      <p className="text-[12px] text-on-surface-variant mt-0.5">{n.message}</p>
                      <p className="text-[11px] text-on-surface-variant/60 mt-1">{n.time}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Auth / User Profile */}
        {isAuthenticated ? (
          <div className="flex items-center gap-3 pl-3 border-l border-outline-variant/20">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-secondary-container to-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs shadow-md flex-shrink-0">
              {initials}
            </div>
            <div className="hidden lg:block text-left">
              <div className="text-xs font-medium text-on-surface">{displayName}</div>
              <div className="text-[10px] font-mono text-primary uppercase tracking-wider">USER</div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 pl-3 border-l border-outline-variant/20">
            <button
              onClick={() => setAuthModalOpen(true)}
              className="px-4 py-1.5 bg-primary-container text-on-primary-container text-[12px] font-bold rounded-xl hover:brightness-110 active:scale-95 transition-all shadow-md shadow-primary-container/20"
            >
              Sign In
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
