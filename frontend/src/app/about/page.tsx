"use client";

import React from "react";

const techStack = [
  { name: "Next.js 15", role: "App Router & SSR", icon: "layers" },
  { name: "Tailwind CSS v4", role: "Cyber UI Design System", icon: "palette" },
  { name: "FastAPI", role: "Async Python Backend", icon: "api" },
  { name: "PostgreSQL + pgvector", role: "Relational & Vector Store", icon: "database" },
  { name: "Neo4j GraphRAG", role: "Knowledge Graph Engine", icon: "hub" },
  { name: "Pinecone", role: "1024-d Dense Indexing", icon: "scatter_plot" },
  { name: "Groq Llama 3.3", role: "Real-Time LLM Inference", icon: "psychology" },
  { name: "LangGraph", role: "Agent Orchestration", icon: "account_tree" },
];

export default function AboutPage() {
  return (
    <div className="min-h-full w-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="w-full max-w-4xl mx-auto space-y-6">
        {/* Page header */}
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-primary text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              info
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-[22px] font-bold text-on-surface leading-tight">About</h2>
            <p className="text-[12px] text-on-surface-variant font-mono">Portfolio Showcase · Enterprise Intelligence Studio</p>
          </div>
        </div>

        {/* Hero card */}
        <div className="glass-card w-full p-8 rounded-2xl border border-outline-variant/20 text-center">
          <div className="w-20 h-20 rounded-2xl bg-primary-container mx-auto flex items-center justify-center mb-5 shadow-xl shadow-primary-container/20 overflow-hidden">
            <img src="/vyron-logo.png" alt="Vyron AI" className="w-12 h-12 object-contain" />
          </div>
          <h3 className="text-2xl font-black text-on-surface mb-2 tracking-tight">Vyron AI</h3>
          <p className="text-[14px] text-primary font-mono mb-4">v1.0.0-backend-intelligence · Production Release</p>
          <p className="text-body-md text-on-surface-variant w-full max-w-2xl mx-auto leading-relaxed">
            Vyron AI — an intelligent assistant with long-term memory, RAG-powered knowledge search, Neo4j graph traversal, and real-time SSE streaming — engineered end-to-end for production reliability and speed.
          </p>
        </div>

        {/* Tech stack */}
        <div className="glass-card w-full p-6 rounded-2xl border border-outline-variant/20">
          <h3 className="text-[15px] font-bold text-on-surface mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">stack</span>
            Technology Stack
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 w-full">
            {techStack.map((tech) => (
              <div key={tech.name} className="flex items-center gap-3 p-3.5 rounded-xl bg-surface-container-high border border-outline-variant/10 hover:border-primary/20 transition-colors w-full">
                <div className="w-9 h-9 rounded-lg bg-primary-container/20 flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-primary text-[18px]">{tech.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-on-surface truncate">{tech.name}</p>
                  <p className="text-[11px] text-on-surface-variant truncate">{tech.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Author */}
        <div className="glass-card w-full p-6 rounded-2xl border border-outline-variant/20 flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-secondary-container to-primary-container flex items-center justify-center flex-shrink-0 shadow-lg">
            <span className="text-xl font-black text-on-primary-container">AM</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[15px] font-bold text-on-surface">Anvesh Mishra</p>
            <p className="text-[13px] text-on-surface-variant mt-0.5 truncate">Architect & Engineer · Vyron AI Platform</p>
            <p className="text-[11px] font-mono text-primary mt-1">anvesh@vyron.ai</p>
          </div>
        </div>
      </div>
    </div>
  );
}
