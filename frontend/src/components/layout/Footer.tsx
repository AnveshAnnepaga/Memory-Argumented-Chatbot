'use client';

import React from 'react';
import { Terminal, Heart, GitBranch, ShieldAlert } from 'lucide-react';

export function Footer() {
  return (
    <footer className="h-12 px-6 border-t border-white/10 bg-slate-950/80 flex items-center justify-between text-xs font-mono text-slate-400 z-30">
      <div className="flex items-center space-x-3">
        <span className="flex items-center text-cyan-400">
          <Terminal className="w-3.5 h-3.5 mr-1" />
          Antigravity Engine
        </span>
        <span className="text-slate-600">|</span>
        <span className="text-slate-400">Milestone 15 — Productization & Production Deployment</span>
      </div>

      <div className="flex items-center space-x-4 hidden md:flex">
        <span className="flex items-center text-slate-400">
          <GitBranch className="w-3.5 h-3.5 mr-1 text-blue-400" />
          Branch: <strong className="text-white ml-1">main (v1.0.0-backend-intelligence)</strong>
        </span>
        <span className="text-slate-600">|</span>
        <span className="flex items-center text-slate-300">
          Built with <Heart className="w-3.5 h-3.5 mx-1 text-pink-500 inline fill-pink-500" /> by <strong className="text-cyan-400 ml-1">Anvesh Mishra</strong>
        </span>
      </div>
    </footer>
  );
}
