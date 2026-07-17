"use client";

import React from "react";

export default function EvaluationPage() {
  return (
    <main className="ml-64 pt-16 min-h-screen bg-background text-on-surface pb-24">
      <header className="fixed top-0 left-64 right-0 z-50 h-16 flex items-center px-lg backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[24px]">analytics</span>
          <h2 className="text-headline-md font-headline-md font-bold text-on-surface">Evaluation</h2>
        </div>
      </header>

      <div className="max-w-4xl mx-auto pt-24 px-lg">
        <div className="glass-card p-xl rounded-2xl border border-outline-variant/20 text-center">
          <span className="material-symbols-outlined text-primary text-5xl mb-md" style={{ fontVariationSettings: "'FILL' 1" }}>analytics</span>
          <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">Evaluation</h3>
          <p className="text-body-md text-on-surface-variant max-w-md mx-auto">
            Monitor response quality and system performance metrics.
          </p>
        </div>
      </div>
    </main>
  );
}
