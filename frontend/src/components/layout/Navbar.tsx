'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { ShieldCheck, Bell, User, Zap, Radio } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Platform Overview & Architecture', subtitle: 'Real-Time 6-Layer Intelligence Orchestration Engine' },
  '/chat': { title: 'Neural Chat & Reasoning Studio', subtitle: 'Live SSE Streaming, RAG Citations & Graph Traversal Timeline' },
  '/history': { title: 'Conversation History & Archive', subtitle: 'Manage, Pin, Search, and Export Multi-Turn Sessions' },
  '/memory': { title: 'Long-Term Memory Dashboard', subtitle: 'User Profile, Semantic Facts, Episodes & Forgetting Curves' },
  '/knowledge': { title: 'Knowledge Base & Ingestion Registry', subtitle: 'Pinecone Vector Indexing (`1024-d`), Chunks & Source Management' },
  '/graph': { title: 'Neo4j GraphRAG Visualizer', subtitle: 'Interactive Force-Directed Knowledge Graph Traversal & Entity Explorer' },
  '/evaluation': { title: 'Evaluation & Observability Platform', subtitle: 'Real-Time Latency Breakdown, RAG/Graph Accuracy & Hallucination Scoring' },
  '/admin': { title: 'Admin Control Center', subtitle: 'Trigger Re-Indexing, Graph Synchronization, Memory Cleanup & Feature Flags' },
  '/settings': { title: 'System Configuration & Cost Parameters', subtitle: 'Configure LLM Token Rates, API Endpoints & System Limits' },
  '/about': { title: 'About & Portfolio Showcase', subtitle: 'Designed and Engineered by Anvesh Mishra (Milestones 1–15)' },
};

export function Navbar() {
  const pathname = usePathname();
  const { user, systemHealth, notifications } = useAppStore();

  const current = PAGE_TITLES[pathname] || {
    title: 'Antigravity AI Platform',
    subtitle: 'Production Intelligence Studio',
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-white/10 glass-panel bg-slate-950/70">
      {/* Page Title Header */}
      <div>
        <h1 className="text-base font-semibold tracking-wide text-white glow-text-cyan flex items-center space-x-2.5">
          <span>{current.title}</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            FASTAPI / NEXT.JS 15
          </span>
        </h1>
        <p className="text-xs text-slate-400 font-mono hidden sm:block">{current.subtitle}</p>
      </div>

      {/* Right Controls & Status Bar */}
      <div className="flex items-center space-x-4">
        {/* Live SSE / WebSocket status indicator */}
        <div className="hidden md:flex items-center px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/10 space-x-2">
          <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span className="text-[11px] font-mono text-slate-300">
            API STATUS: <span className="text-emerald-400 font-bold">ONLINE (8000)</span>
          </span>
        </div>

        {/* System Health Badge */}
        <div className="flex items-center px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-semibold space-x-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>{systemHealth}</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            className="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 transition-colors relative"
            title="System Notifications"
          >
            <Bell className="w-4 h-4" />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-pink-500 text-[10px] font-bold text-white flex items-center justify-center animate-bounce">
                {notifications.length}
              </span>
            )}
          </button>
        </div>

        {/* User Profile Chip */}
        <div className="flex items-center space-x-3 pl-2 border-l border-white/10">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xs shadow-md">
            AM
          </div>
          <div className="hidden lg:block text-left">
            <div className="text-xs font-medium text-slate-200">{user?.name || 'Anvesh Mishra'}</div>
            <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">{user?.role || 'ARCHITECT'}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
