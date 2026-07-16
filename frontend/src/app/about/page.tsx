"use client";

import React from "react";
import Link from "next/link";

export default function AboutPage() {
  const milestones = [
    { num: "01–04", title: "FastAPI Architecture, Config, Infrastructure & Repository Layer", status: "VERIFIED", desc: "Asynchronous server foundation with custom exception handlers, Pydantic V2 validation, and asyncpg/motor database connections." },
    { num: "05–08", title: "Knowledge Ingestion, Pinecone Hybrid RAG & Neo4j GraphRAG", status: "VERIFIED", desc: "1024-d BAAI/bge vector embeddings (`Pinecone`), BM25 sparse keyword indices, RRF fusion, and Cypher multi-hop graph queries." },
    { num: "11", title: "LangGraph Orchestration Brain", status: "VERIFIED", desc: "Stateful DAG conditional routing between direct LLM, Long-Term Memory, Specialized Tools, and Hybrid RAG retrieval paths." },
    { num: "12", title: "PostgreSQL Long-Term Memory System", status: "VERIFIED", desc: "User profile synthesis, semantic fact deduplication (`confidence & importance scores`), episodic logs, and Ebbinghaus forgetting curves." },
    { num: "13", title: "Tool Execution Framework", status: "VERIFIED", desc: "Decoupled tool modules (`CalculatorTool`, `WebSearchTool`, `SQLQueryTool`, `GraphCypherTool`) with zero coupling to orchestration logic." },
    { num: "14", title: "Evaluation, Monitoring & Observability Platform", status: 'VERIFIED', desc: "Read-only hooks measuring Hallucination, Groundedness, warm vs cold latency breakdowns, and dynamic token cost tracking." },
    { num: "15", title: "Productization, Next.js 15 Cyber UI & Production Deployment", status: "VERIFIED", desc: "Glassmorphism dark-mode Next.js 15 App Router frontend with real-time SSE streaming, Docker containerization, and NGINX reverse proxy." },
  ];

  const techStack = [
    { name: "FastAPI (Python 3.11+)", category: "Backend REST & SSE Server" },
    { name: "Next.js 15 (App Router)", category: "Frontend React 19 UI" },
    { name: "LangGraph StateGraph", category: "Reasoning Orchestration DAG" },
    { name: "Pinecone Vector Index", category: "Dense 1024-d Embeddings" },
    { name: "Neo4j Graph Database", category: "GraphRAG Multi-Hop Entities" },
    { name: "PostgreSQL + asyncpg", category: "Long-Term Memory & User Profiles" },
    { name: "Groq API (Llama-3-70B)", category: "High-Throughput LLM Inference" },
    { name: "Tailwind CSS v4 + Lucide", category: "Cyber Glassmorphism Styling" },
    { name: "Zustand + TanStack Query", category: "State Management & Caching" },
    { name: "Docker + NGINX", category: "Containerized Production Deployment" },
  ];

  return (
    <main className="ml-64 pt-16 min-h-screen bg-background text-on-surface pb-24">
      {/* Top Header Bar */}
      <header className="h-16 border-b border-outline-variant/20 bg-surface-container/50 backdrop-blur-md flex items-center justify-between px-lg fixed top-0 right-0 left-64 z-30">
        <div className="flex items-center gap-md">
          <span className="text-headline-md font-headline-md font-bold text-on-surface">About Platform OS</span>
          <span className="text-label-md px-2.5 py-0.5 bg-primary-container/10 text-primary border border-primary/20 rounded-full font-bold">
            Version 15.0 Production
          </span>
        </div>
        <div className="flex items-center gap-sm">
          <Link
            href="/chat"
            className="px-4 py-1.5 rounded-xl bg-primary text-on-primary text-label-md font-bold flex items-center gap-2 transition-all cursor-pointer shadow-md shadow-primary/20"
          >
            <span className="material-symbols-outlined text-[18px]">forum</span>
            <span>Launch Studio</span>
          </Link>
        </div>
      </header>

      <div className="p-lg md:p-margin-desktop max-w-[1600px] mx-auto space-y-lg">
        {/* Author & Project Hero Card */}
        <div className="relative overflow-hidden rounded-3xl border border-outline-variant/30 glass-surface p-8 md:p-12 text-center bg-gradient-to-b from-surface-container/90 via-primary/5 to-surface-dim shadow-2xl">
          <div className="absolute top-4 right-6 text-label-md font-mono-code text-primary bg-primary/10 px-3 py-1 rounded-full border border-primary/20 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
            <span>PRODUCTION v15.0 COMPLETE</span>
          </div>

          <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-gradient-to-tr from-primary to-secondary shadow-[0_0_30px_rgba(0,229,255,0.4)] mb-6">
            <span className="material-symbols-outlined text-on-primary text-[32px]">terminal</span>
          </div>

          <h1 className="text-display-sm md:text-display-md font-extrabold tracking-tight text-on-surface max-w-3xl mx-auto">
            Antigravity Intelligence Engine
          </h1>
          <p className="mt-4 text-body-lg text-on-surface-variant max-w-2xl mx-auto leading-relaxed">
            A production-grade, multi-module Enterprise AI Architecture designed and built by <strong className="text-primary font-bold">Anvesh Mishra</strong>. Combining state-of-the-art hybrid search, graph reasoning, and episodic memory into an autonomous system.
          </p>
        </div>

        {/* Milestones Verification Timeline */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 border-b border-outline-variant/20 pb-3">
            <span className="material-symbols-outlined text-primary text-[24px]">verified</span>
            <h2 className="text-headline-lg font-bold text-on-surface">Milestone Verification Matrix (`01 – 15`)</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {milestones.map((m, i) => (
              <div key={i} className="glass-surface p-6 rounded-2xl border border-outline-variant/20 shadow-md flex flex-col justify-between space-y-4 hover:border-primary/40 transition-all">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-label-md font-mono-code font-bold text-primary bg-primary/10 px-2.5 py-1 rounded-lg border border-primary/20">
                      Milestone {m.num}
                    </span>
                    <span className="text-[11px] font-mono-code font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/30 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">check_circle</span>
                      {m.status}
                    </span>
                  </div>
                  <h3 className="text-headline-md font-bold text-on-surface leading-snug">{m.title}</h3>
                  <p className="text-body-sm text-on-surface-variant leading-relaxed font-mono-code">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Technical Architecture Matrix */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 border-b border-outline-variant/20 pb-3">
            <span className="material-symbols-outlined text-secondary text-[24px]">layers</span>
            <h2 className="text-headline-lg font-bold text-on-surface">Full-Stack Technology Stack</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {techStack.map((t, idx) => (
              <div key={idx} className="glass-surface p-4 rounded-xl border border-outline-variant/10 shadow-sm flex flex-col justify-center text-center space-y-1">
                <span className="text-body-sm font-bold text-on-surface truncate">{t.name}</span>
                <span className="text-[11px] text-on-surface-variant/70 font-mono-code truncate">{t.category}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
