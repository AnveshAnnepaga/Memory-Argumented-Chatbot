"use client";

import React from "react";

export default function AdminPage() {
  return (
    <main className="ml-64 pt-16 min-h-screen bg-background text-on-surface pb-24">
      <header className="fixed top-0 left-64 right-0 z-50 h-16 flex items-center px-lg backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[24px]">account_circle</span>
          <h2 className="text-headline-md font-headline-md font-bold text-on-surface">Profile</h2>
        </div>
      </header>

      <div className="max-w-2xl mx-auto pt-24 px-lg">
        <div className="glass-card p-xl rounded-2xl border border-outline-variant/20">
          <div className="flex items-center gap-lg mb-xl">
            <div className="w-20 h-20 rounded-full bg-primary-container/20 flex items-center justify-center border-2 border-primary/30">
              <span className="material-symbols-outlined text-primary text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>account_circle</span>
            </div>
            <div>
              <h3 className="text-headline-lg font-headline-lg text-on-surface">User</h3>
              <p className="text-body-md text-on-surface-variant">user@example.com</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
