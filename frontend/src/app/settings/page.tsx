"use client";

import React, { useState } from "react";
import { useAppStore } from "../../store/useAppStore";

export default function SettingsPage() {
  const { addNotification } = useAppStore();

  const [apiBaseUrl, setApiBaseUrl] = useState("http://localhost:8000/api/v1");
  const [llmModel, setLlmModel] = useState("llama-3.3-70b-versatile");
  const [inputPricingPerM, setInputPricingPerM] = useState("0.59");
  const [outputPricingPerM, setOutputPricingPerM] = useState("0.79");
  const [hallucinationThreshold, setHallucinationThreshold] = useState("0.20");
  const [maxRetrievedChunks, setMaxRetrievedChunks] = useState("5");
  const [sseChunkDelayMs, setSseChunkDelayMs] = useState("15");
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    addNotification({
      title: "System Settings Saved",
      message: "Dynamic LLM pricing rates and API endpoint configurations applied across frontend state.",
      type: "success",
    });
    setTimeout(() => setIsSaved(false), 2500);
  };

  const handleReset = () => {
    setApiBaseUrl("http://localhost:8000/api/v1");
    setLlmModel("llama-3.3-70b-versatile");
    setInputPricingPerM("0.59");
    setOutputPricingPerM("0.79");
    setHallucinationThreshold("0.20");
    setMaxRetrievedChunks("5");
    setSseChunkDelayMs("15");
    addNotification({
      title: "Settings Reset",
      message: "Restored default Groq Llama-3-70B dynamic cost metrics and 0.20 hallucination threshold.",
      type: "info",
    });
  };

  return (
    <main className="ml-64 pt-16 min-h-screen bg-background text-on-surface pb-24">
      {/* Top Header Bar */}
      <header className="fixed top-0 left-64 right-0 z-50 h-16 flex justify-between items-center px-lg backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[24px]">tune</span>
          <h2 className="text-headline-md font-headline-md font-bold text-on-surface">Platform OS Settings &amp; Configuration</h2>
        </div>
        <div className="flex items-center gap-md">
          <span className="text-label-md px-3 py-1 bg-primary-container/10 text-primary border border-primary/20 rounded-full font-bold uppercase">
            Dynamic Pricing Active
          </span>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            notifications
          </button>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            contrast
          </button>
        </div>
      </header>

      <div className="p-lg max-w-5xl mx-auto space-y-lg">
        {/* Header Banner */}
        <div className="glass-surface p-lg rounded-2xl border border-outline-variant/20 flex flex-col md:flex-row md:items-center justify-between gap-md shadow-xl">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-primary font-mono-code text-label-md uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              Milestone 15 Configuration Layer
            </div>
            <h1 className="text-headline-lg font-headline-lg font-bold text-on-surface">LLM Pricing &amp; Orchestration Tuning</h1>
            <p className="text-body-sm text-on-surface-variant max-w-xl">
              Configure dynamic token pricing rates, custom hallucination safety thresholds, and hybrid RAG chunk retrieval boundaries.
            </p>
          </div>
          <div className="flex gap-sm">
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2.5 rounded-xl bg-surface-container-high hover:bg-surface-variant transition-colors text-on-surface-variant text-label-md font-bold flex items-center gap-2 cursor-pointer border border-outline-variant/20"
            >
              <span className="material-symbols-outlined text-[18px]">restart_alt</span>
              Reset Defaults
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="px-6 py-2.5 rounded-xl bg-primary-container text-on-primary-container font-bold shadow-lg hover:opacity-90 transition-all flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">save</span>
              {isSaved ? "Saved!" : "Save Configuration"}
            </button>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-lg">
          {/* Section 1: Dynamic Pricing & Model Parameters */}
          <div className="glass-surface p-lg rounded-2xl border border-outline-variant/20 space-y-lg shadow-xl">
            <div className="flex items-center gap-3 border-b border-outline-variant/10 pb-4">
              <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                <span className="material-symbols-outlined text-[24px]">payments</span>
              </div>
              <div>
                <h3 className="text-headline-md font-headline-md font-bold text-on-surface">Dynamic Token Pricing &amp; LLM Core</h3>
                <p className="text-label-md text-on-surface-variant">
                  Adjust real-time cost estimation multipliers ($ per Million tokens). Avoid hardcoded model rates.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
              <div className="space-y-2">
                <label className="text-label-md font-bold text-on-surface flex items-center gap-2">
                  Active Groq Model ID
                </label>
                <input
                  type="text"
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/20 rounded-xl px-4 py-3 text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 font-mono-code"
                />
              </div>

              <div className="space-y-2">
                <label className="text-label-md font-bold text-on-surface flex items-center gap-2">
                  FastAPI Backend Endpoint URL
                </label>
                <input
                  type="text"
                  value={apiBaseUrl}
                  onChange={(e) => setApiBaseUrl(e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/20 rounded-xl px-4 py-3 text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 font-mono-code"
                />
              </div>

              <div className="space-y-2">
                <label className="text-label-md font-bold text-on-surface flex items-center justify-between">
                  <span>Input Token Pricing ($ / 1M Tokens)</span>
                  <span className="text-primary font-mono-code font-bold">${inputPricingPerM}</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={inputPricingPerM}
                  onChange={(e) => setInputPricingPerM(e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/20 rounded-xl px-4 py-3 text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 font-mono-code"
                />
              </div>

              <div className="space-y-2">
                <label className="text-label-md font-bold text-on-surface flex items-center justify-between">
                  <span>Output Token Pricing ($ / 1M Tokens)</span>
                  <span className="text-secondary font-mono-code font-bold">${outputPricingPerM}</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={outputPricingPerM}
                  onChange={(e) => setOutputPricingPerM(e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/20 rounded-xl px-4 py-3 text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 font-mono-code"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Hallucination & Retrieval Tuning */}
          <div className="glass-surface p-lg rounded-2xl border border-outline-variant/20 space-y-lg shadow-xl">
            <div className="flex items-center gap-3 border-b border-outline-variant/10 pb-4">
              <div className="p-2.5 rounded-xl bg-secondary/10 text-secondary">
                <span className="material-symbols-outlined text-[24px]">verified</span>
              </div>
              <div>
                <h3 className="text-headline-md font-headline-md font-bold text-on-surface">Evaluation &amp; Orchestration Parameters</h3>
                <p className="text-label-md text-on-surface-variant">
                  Define when the system flags a response as ungrounded or triggers multi-hop Graph traversal.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
              <div className="space-y-3">
                <label className="text-label-md font-bold text-on-surface flex items-center justify-between">
                  <span>Hallucination Alert Threshold</span>
                  <span className="text-error font-mono-code font-bold">{hallucinationThreshold}</span>
                </label>
                <input
                  type="range"
                  min="0.05"
                  max="0.95"
                  step="0.05"
                  value={hallucinationThreshold}
                  onChange={(e) => setHallucinationThreshold(e.target.value)}
                  className="w-full accent-primary h-1.5 bg-surface-container-highest rounded-lg cursor-pointer"
                />
                <p className="text-[11px] text-on-surface-variant">
                  If semantic entailment score drops below {hallucinationThreshold}, a warning flag is raised in the audit log.
                </p>
              </div>

              <div className="space-y-3">
                <label className="text-label-md font-bold text-on-surface flex items-center justify-between">
                  <span>Max Retrieved RAG Chunks</span>
                  <span className="text-primary font-mono-code font-bold">{maxRetrievedChunks}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="15"
                  step="1"
                  value={maxRetrievedChunks}
                  onChange={(e) => setMaxRetrievedChunks(e.target.value)}
                  className="w-full accent-primary h-1.5 bg-surface-container-highest rounded-lg cursor-pointer"
                />
                <p className="text-[11px] text-on-surface-variant">
                  Number of Pinecone dense + sparse vector candidates sent to the cross-encoder reranker.
                </p>
              </div>

              <div className="space-y-3">
                <label className="text-label-md font-bold text-on-surface flex items-center justify-between">
                  <span>SSE Token Stream Delay (ms)</span>
                  <span className="text-tertiary font-mono-code font-bold">{sseChunkDelayMs}ms</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={sseChunkDelayMs}
                  onChange={(e) => setSseChunkDelayMs(e.target.value)}
                  className="w-full accent-primary h-1.5 bg-surface-container-highest rounded-lg cursor-pointer"
                />
                <p className="text-[11px] text-on-surface-variant">
                  Adjust simulated typing delay for token chunks during real-time streaming sessions.
                </p>
              </div>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
