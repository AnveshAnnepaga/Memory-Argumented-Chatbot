"use client";

import React from "react";
import Link from "next/link";
import Aurora3DParticles from "@/components/Aurora3DParticles";

export default function HomePage() {
  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col font-body-md overflow-x-hidden w-full">
      <header className="sticky top-0 z-50 h-20 bg-background/80 backdrop-blur-md border-b border-outline-variant/20 flex items-center justify-between px-6 sm:px-12 w-full">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-container flex items-center justify-center shadow-lg shadow-primary-container/20 flex-shrink-0 overflow-hidden">
            <img src="/vyron-logo.png" alt="Vyron" className="w-7 h-7 object-contain" />
          </div>
          <span className="text-[18px] font-bold text-primary tracking-tight">Vyron AI</span>
        </div>
        
        <div className="hidden md:flex items-center gap-8">
          <Link className="text-[14px] font-bold text-primary transition-colors duration-200" href="/">Home</Link>
          <Link className="text-[14px] text-on-surface-variant hover:text-primary transition-colors duration-200" href="/chat">Chat</Link>
          <Link className="text-[14px] text-on-surface-variant hover:text-primary transition-colors duration-200" href="/knowledge">Knowledge</Link>
          <Link className="text-[14px] text-on-surface-variant hover:text-primary transition-colors duration-200" href="/memory">Memory</Link>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/chat" className="px-5 py-2.5 bg-primary-container text-on-primary-container font-bold text-[13px] rounded-xl hover:brightness-110 active:scale-95 transition-all shadow-md shadow-primary-container/20 flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">play_arrow</span>
            Get Started
          </Link>
        </div>
      </header>

      <main className="relative flex-1 flex flex-col items-center justify-center overflow-hidden w-full min-h-[calc(100vh-160px)] py-16">
        <Aurora3DParticles />
        
        <div className="relative z-10 flex flex-col items-center text-center px-6 max-w-4xl mx-auto w-full">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-on-surface mb-6 leading-tight tracking-tight">
            Vyron AI with <span className="text-primary text-glow whitespace-nowrap">Long-Term Memory</span>
          </h1>
          <p className="text-lg sm:text-xl text-on-surface-variant mb-10 w-full max-w-2xl mx-auto leading-relaxed">
            An intelligent assistant that remembers context, searches knowledge, and helps you get things done across every conversation.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full max-w-md mx-auto">
            <Link href="/chat" className="w-full sm:w-auto px-8 py-3.5 bg-primary-container text-on-primary-container font-bold text-sm rounded-xl hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-primary-container/20 text-center flex items-center justify-center gap-2">
              <span className="material-symbols-outlined text-[18px]">forum</span>
              Start Chatting
            </Link>
            <Link href="/knowledge" className="w-full sm:w-auto px-8 py-3.5 bg-surface-container-high border border-outline-variant/30 text-on-surface font-bold text-sm rounded-xl hover:border-primary/50 active:scale-95 transition-all text-center flex items-center justify-center gap-2">
              <span className="material-symbols-outlined text-[18px]">auto_stories</span>
              Explore Knowledge
            </Link>
          </div>
        </div>
      </main>

      <footer className="bg-surface-container-lowest py-10 border-t border-outline-variant/15 w-full mt-auto">
        <div className="px-6 sm:px-12 max-w-6xl mx-auto w-full">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center overflow-hidden">
                <img src="/vyron-logo.png" alt="Vyron" className="w-5 h-5 object-contain" />
              </div>
              <span className="text-[15px] font-bold text-primary">Vyron AI</span>
            </div>
            <div className="flex items-center gap-8">
              <Link className="text-[13px] text-on-surface-variant hover:text-primary transition-colors" href="/chat">Chat</Link>
              <Link className="text-[13px] text-on-surface-variant hover:text-primary transition-colors" href="/knowledge">Knowledge</Link>
              <Link className="text-[13px] text-on-surface-variant hover:text-primary transition-colors" href="/memory">Memory</Link>
            </div>
            <span className="text-[12px] text-on-surface-variant/70 font-mono">&copy; 2026 Vyron AI. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
