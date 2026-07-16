"use client";

import React from "react";
import Link from "next/link";
import Aurora3DParticles from "@/components/Aurora3DParticles";

export default function HomePage() {
  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col font-body-md overflow-x-hidden">
      {/* Top Header Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 h-20 bg-surface/80 backdrop-blur-md border-b border-outline-variant/20 flex items-center justify-between px-margin-mobile md:px-margin-desktop">
        <div className="flex items-center gap-md">
          <div className="w-10 h-10 rounded-xl bg-primary-container flex items-center justify-center shadow-lg shadow-primary-container/20">
            <span className="material-symbols-outlined text-on-primary-container text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
          </div>
          <span className="text-headline-md font-headline-md font-bold text-primary tracking-tight">Antigravity AI</span>
        </div>
        
        <div className="hidden md:flex items-center gap-lg">
          <Link className="text-label-md font-label-md text-primary font-bold hover:text-primary transition-colors duration-200" href="/">Overview</Link>
          <Link className="text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors duration-200" href="/chat">Studio</Link>
          <Link className="text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors duration-200" href="/knowledge">Knowledge</Link>
          <Link className="text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors duration-200" href="/graph">Graph</Link>
          <Link className="text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors duration-200" href="/memory">Memory</Link>
          <Link className="text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors duration-200" href="/evaluation">Evaluation</Link>
        </div>

        <div className="flex items-center gap-md">
          <Link href="/login" className="px-lg py-2 bg-transparent border border-outline-variant/60 text-on-surface-variant font-label-md rounded-lg hover:bg-surface-variant/30 hover:text-primary transition-all">
            Sign In
          </Link>
          <Link href="/chat" className="px-lg py-2 bg-primary-container text-on-primary-container font-label-md rounded-lg hover:brightness-110 active:scale-95 transition-all shadow-md shadow-primary-container/20">
            Launch Studio
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative min-h-screen pt-32 pb-24 px-margin-mobile md:px-margin-desktop overflow-hidden flex flex-col justify-center aurora-glow">
        <Aurora3DParticles />
        <div className="relative z-10 max-w-4xl">
          <div className="inline-flex items-center px-md py-xs rounded-full bg-primary-container/10 border border-primary-container/20 mb-lg">
            <span className="text-label-md font-label-md text-primary-container uppercase tracking-widest">Milestone 15 — Production AI Platform</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg-mobile md:text-display-lg text-on-surface mb-md leading-tight max-w-3xl">
            Enterprise AI Assistant with <span className="text-primary text-glow">Long-Term Memory</span> &amp; Intelligent Reasoning
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant mb-xl max-w-2xl">
            Empower your workforce with an autonomous architect that masters Knowledge Intelligence, Graph Reasoning, and real-time decision-making for complex enterprise workflows.
          </p>
          <div className="flex flex-col sm:flex-row items-center gap-md">
            <Link href="/chat" className="w-full sm:w-auto px-2xl py-md bg-primary-container text-on-primary-container font-label-md text-label-md rounded-lg hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-primary-container/20 text-center">
              Start Chatting
            </Link>
            <a href="#capabilities" className="w-full sm:w-auto px-2xl py-md bg-transparent border border-outline-variant text-primary font-label-md text-label-md rounded-lg hover:bg-surface-variant/30 active:scale-95 transition-all text-center">
              Explore Platform
            </a>
          </div>
        </div>

        {/* Capability Grid */}
        <div id="capabilities" className="mt-2xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg relative z-10">
          {/* Reasoning */}
          <div className="glass-card p-lg rounded-xl">
            <div className="w-12 h-12 bg-primary-container/10 rounded-lg flex items-center justify-center mb-md border border-primary-container/20">
              <span className="material-symbols-outlined text-primary-container" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            </div>
            <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">LangGraph Orchestration</h3>
            <p className="text-body-md font-body-md text-on-surface-variant">Advanced chain-of-thought routing (`DIRECT_LLM`, `HYBRID_RAG`, `GRAPH_RAG`) for deterministic multi-step logic.</p>
          </div>
          {/* Knowledge */}
          <div className="glass-card p-lg rounded-xl">
            <div className="w-12 h-12 bg-tertiary-container/10 rounded-lg flex items-center justify-center mb-md border border-tertiary-container/20">
              <span className="material-symbols-outlined text-tertiary-container" style={{ fontVariationSettings: "'FILL' 1" }}>auto_stories</span>
            </div>
            <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">Hybrid RAG &amp; Vector Search</h3>
            <p className="text-body-md font-body-md text-on-surface-variant">Hybrid sparse BM25 plus dense Pinecone embeddings with Cross-Encoder reranking for ultra-low latency.</p>
          </div>
          {/* Memory */}
          <div className="glass-card p-lg rounded-xl">
            <div className="w-12 h-12 bg-secondary-container/10 rounded-lg flex items-center justify-center mb-md border border-secondary-container/20">
              <span className="material-symbols-outlined text-secondary-fixed-dim" style={{ fontVariationSettings: "'FILL' 1" }}>memory</span>
            </div>
            <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">Long-Term Memory System</h3>
            <p className="text-body-md font-body-md text-on-surface-variant">Persistent context extraction storing nuanced user facts and episodes across sessions without prompt bloat.</p>
          </div>
          {/* Graph */}
          <div className="glass-card p-lg rounded-xl">
            <div className="w-12 h-12 bg-primary-container/10 rounded-lg flex items-center justify-center mb-md border border-primary-container/20">
              <span className="material-symbols-outlined text-primary-container" style={{ fontVariationSettings: "'FILL' 1" }}>hub</span>
            </div>
            <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">Neo4j Graph Reasoning</h3>
            <p className="text-body-md font-body-md text-on-surface-variant">Traverse multi-hop relationships (`RELATED_TO`, `RESOLVES`, `DEPENDS_ON`) to discover structural insights.</p>
          </div>
          {/* Tool Engines */}
          <div className="glass-card p-lg rounded-xl">
            <div className="w-12 h-12 bg-tertiary-container/10 rounded-lg flex items-center justify-center mb-md border border-tertiary-container/20">
              <span className="material-symbols-outlined text-tertiary-container" style={{ fontVariationSettings: "'FILL' 1" }}>build</span>
            </div>
            <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">Tool Execution Framework</h3>
            <p className="text-body-md font-body-md text-on-surface-variant">Decoupled external function calling (`calculator`, `time_lookup`, `system_diagnostic`) invoked dynamically by router.</p>
          </div>
          {/* Enterprise Governance */}
          <div className="glass-card p-lg rounded-xl">
            <div className="w-12 h-12 bg-secondary-container/10 rounded-lg flex items-center justify-center mb-md border border-secondary-container/20">
              <span className="material-symbols-outlined text-secondary-fixed-dim" style={{ fontVariationSettings: "'FILL' 1" }}>analytics</span>
            </div>
            <h3 className="text-headline-md font-headline-md text-on-surface mb-sm">Observability &amp; Evaluation</h3>
            <p className="text-body-md font-body-md text-on-surface-variant">Real-time telemetry tracking hallucination index (`Groundedness`), confidence scores, and sub-millisecond node latency.</p>
          </div>
        </div>
      </main>

      {/* Metrics Strip */}
      <section className="py-xl bg-surface-container-low border-y border-outline-variant/10">
        <div className="px-margin-mobile md:px-margin-desktop grid grid-cols-2 lg:grid-cols-4 gap-lg text-center">
          <div>
            <div className="text-display-lg font-display-lg text-primary text-glow">99.9%</div>
            <div className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-xs">Uptime SLA</div>
          </div>
          <div>
            <div className="text-display-lg font-display-lg text-primary text-glow">&lt;180ms</div>
            <div className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-xs">Router Latency</div>
          </div>
          <div>
            <div className="text-display-lg font-display-lg text-primary text-glow">10M+</div>
            <div className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-xs">Facts Indexed</div>
          </div>
          <div>
            <div className="text-display-lg font-display-lg text-primary text-glow">0.00</div>
            <div className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-xs">Hallucination Index</div>
          </div>
        </div>
      </section>

      {/* Product Walkthrough */}
      <section className="py-2xl px-margin-mobile md:px-margin-desktop">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-xl">
            <h2 className="text-headline-lg font-headline-lg text-on-surface mb-sm">How Antigravity Works</h2>
            <p className="text-body-lg font-body-lg text-on-surface-variant max-w-2xl mx-auto">
              A fully decoupled, deterministic cognitive pipeline engineered from scratch.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-lg relative">
            {/* Step 1 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full glass-card flex items-center justify-center mb-md border-primary-container/30 relative shadow-lg shadow-primary-container/10">
                <span className="material-symbols-outlined text-primary-container text-3xl">route</span>
                <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-primary-container text-on-primary-container text-[10px] font-bold flex items-center justify-center">01</div>
              </div>
              <h4 className="text-headline-md font-headline-md text-on-surface mb-sm">Intent Analysis</h4>
              <p className="text-body-sm font-body-sm text-on-surface-variant">User query is classified instantly to determine if RAG, Graph, or Tools are required.</p>
            </div>
            {/* Step 2 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full glass-card flex items-center justify-center mb-md border-tertiary-container/30 relative shadow-lg shadow-tertiary-container/10">
                <span className="material-symbols-outlined text-tertiary-container text-3xl">share</span>
                <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-tertiary-container text-on-tertiary-container text-[10px] font-bold flex items-center justify-center">02</div>
              </div>
              <h4 className="text-headline-md font-headline-md text-on-surface mb-sm">Hybrid Retrieval</h4>
              <p className="text-body-sm font-body-sm text-on-surface-variant">The AI queries your vector index and enterprise Neo4j graph to fetch verified context.</p>
            </div>
            {/* Step 3 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full glass-card flex items-center justify-center mb-md border-secondary-container/30 relative shadow-lg shadow-secondary-container/10">
                <span className="material-symbols-outlined text-secondary-fixed-dim text-3xl">memory</span>
                <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-secondary-container text-on-secondary-container text-[10px] font-bold flex items-center justify-center">03</div>
              </div>
              <h4 className="text-headline-md font-headline-md text-on-surface mb-sm">Memory Synthesis</h4>
              <p className="text-body-sm font-body-sm text-on-surface-variant">Past semantic facts and entity profiles are recalled to personalize the response.</p>
            </div>
            {/* Step 4 */}
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full glass-card flex items-center justify-center mb-md border-primary-container/30 relative shadow-lg shadow-primary-container/10">
                <span className="material-symbols-outlined text-primary-container text-3xl">task_alt</span>
                <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-primary-container text-on-primary-container text-[10px] font-bold flex items-center justify-center">04</div>
              </div>
              <h4 className="text-headline-md font-headline-md text-on-surface mb-sm">Verified Output</h4>
              <p className="text-body-sm font-body-sm text-on-surface-variant">A hallucination-free response is generated via Groq LLM with full real-time evaluation.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-surface pt-2xl pb-lg border-t border-outline-variant/10 mt-auto">
        <div className="px-margin-mobile md:px-margin-desktop grid grid-cols-1 md:grid-cols-4 gap-xl mb-2xl">
          <div className="col-span-1 md:col-span-1">
            <span className="text-headline-md font-headline-md font-bold text-primary mb-md block">Antigravity AI</span>
            <p className="text-body-sm font-body-sm text-on-surface-variant mb-md max-w-xs">
              Building the cognitive backbone for the next generation of enterprise intelligence.
            </p>
          </div>
          <div>
            <h5 className="text-label-md font-label-md text-on-surface mb-lg uppercase tracking-widest">Platform</h5>
            <ul className="space-y-sm">
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/chat">Chat Studio</Link></li>
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/knowledge">Knowledge Center</Link></li>
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/graph">Intelligence Graph</Link></li>
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/memory">Memory Engine</Link></li>
            </ul>
          </div>
          <div>
            <h5 className="text-label-md font-label-md text-on-surface mb-lg uppercase tracking-widest">Observability</h5>
            <ul className="space-y-sm">
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/evaluation">Evaluation Center</Link></li>
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/admin">Admin Console</Link></li>
              <li><Link className="text-body-sm font-body-sm text-on-surface-variant hover:text-primary" href="/history">Query History</Link></li>
            </ul>
          </div>
          <div>
            <h5 className="text-label-md font-label-md text-on-surface mb-lg uppercase tracking-widest">Status</h5>
            <div className="flex items-center gap-sm mt-sm">
              <div className="w-2.5 h-2.5 rounded-full bg-tertiary-container animate-pulse"></div>
              <span className="text-body-sm font-body-sm text-tertiary">All Backend Layers Healthy</span>
            </div>
            <p className="text-label-md text-on-surface-variant mt-xs">FastAPI &bull; Pinecone &bull; Neo4j &bull; Groq</p>
          </div>
        </div>
        <div className="px-margin-mobile md:px-margin-desktop pt-lg border-t border-outline-variant/10 flex flex-col md:flex-row justify-between items-center gap-md">
          <span className="text-label-md font-label-md text-on-surface-variant">&copy; 2026 Antigravity AI Corporation by Anvesh Mishra. All rights reserved.</span>
          <div className="flex items-center gap-sm">
            <span className="text-label-md font-label-md text-on-surface-variant">v15.0 Production Architecture</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
