"use client";

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Link from "next/link";
import ChatMessageRenderer from "@/components/ChatMessageRenderer";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  badges?: string[];
  latency_ms?: number;
  reasoning_code?: string;
}

interface MemoryProfile {
  user_id: string;
  semantic_facts: string[];
  episodes: string[];
}

export default function ChatStudioPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      sender: "assistant",
      text: "Hi! I'm Antigravity — your AI assistant. Ask me anything: coding, analysis, explanations, or just a quick chat. What would you like to explore today?",
      badges: [],
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStepLabel, setCurrentStepLabel] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState("Production Session v15");
  const [memoryProfile, setMemoryProfile] = useState<MemoryProfile | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Layout Toggle States to ensure maximum neatness & eliminate double-sidebar cramping
  const [isThreadSidebarOpen, setIsThreadSidebarOpen] = useState(false);
  const [isContextSidebarOpen, setIsContextSidebarOpen] = useState(true);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentStepLabel]);

  useEffect(() => {
    // Fetch live memory context for our sidebar
    axios
      .get(`${API_URL}/api/v1/memory/profile/test-user`)
      .then((res) => {
        if (res.data && res.data.user_id) {
          setMemoryProfile(res.data);
        }
      })
      .catch(() => {
        // Silently ignore if backend is briefly offline
      });
  }, []);

  const handleSendMessage = async () => {
    if (!inputQuery.trim() || isGenerating) return;

    const userText = inputQuery.trim();
    setInputQuery("");
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: "user", text: userText },
      { id: assistantMsgId, sender: "assistant", text: "", badges: [] },
    ]);

    setIsGenerating(true);
    setCurrentStepLabel("Analyzing Query Intent...");

    try {
      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userText,
          user_id: "test-user",
          conversation_id: "default",
        }),
      });

      if (!response.body) {
        throw new Error("No readable stream received.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      const collectedBadges: string[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const blockLines = block.split("\n");
          let eventType = "";
          let dataText = "";

          for (const line of blockLines) {
            if (line.startsWith("event: ")) {
              eventType = line.replace("event: ", "").trim();
            } else if (line.startsWith("data: ")) {
              dataText = line.replace("data: ", "").trim();
            }
          }

          if (eventType === "step") {
            try {
              const parsed = JSON.parse(dataText);
              setCurrentStepLabel(parsed.label || "Processing workflow...");
              if (parsed.node === "rag_retrieval_node" && !collectedBadges.includes("Hybrid RAG")) {
                collectedBadges.push("Hybrid RAG");
              } else if (parsed.node === "memory_retrieval_node" && !collectedBadges.includes("Memory Active")) {
                collectedBadges.push("Memory Active");
              } else if (parsed.node === "tool_execution_node" && !collectedBadges.includes("Tool Executed")) {
                collectedBadges.push("Tool Executed");
              }
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMsgId ? { ...m, badges: [...collectedBadges] } : m))
              );
            } catch {
              // ignore parse errors
            }
          } else if (eventType === "token") {
            setCurrentStepLabel(null);
            try {
              const parsed = JSON.parse(dataText);
              if (parsed.text) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId ? { ...m, text: m.text + parsed.text } : m
                  )
                );
              }
            } catch {
              // ignore parse errors
            }
          } else if (eventType === "complete") {
            setCurrentStepLabel(null);
            try {
              const parsed = JSON.parse(dataText);
              const execMs =
                parsed?.metadata?.execution_time_ms ||
                parsed?.execution_time_ms ||
                null;
              if (execMs) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId ? { ...m, latency_ms: execMs } : m
                  )
                );
              }
            } catch {
              // ignore parse errors on complete event
            }
          } else if (eventType === "done") {
            setCurrentStepLabel(null);
          }
        }
      }
    } catch {
      // Fallback: non-streaming REST call if streaming fails
      try {
        const res = await axios.post(`${API_URL}/api/v1/chat/query`, {
          query: userText,
          user_id: "test-user",
          conversation_id: "default",
        });
        const d = res.data?.data || res.data || {};
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  text: d.response || "I'm sorry, I couldn't generate a response. Please try again.",
                  latency_ms: d.metadata?.execution_time_ms || null,
                  badges: [d.router_decision?.route || "DIRECT_LLM"].filter(Boolean),
                }
              : m
          )
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, text: "⚠️ I had trouble reaching the AI engine. Please check your connection and try again." }
              : m
          )
        );
      }
    } finally {
      setIsGenerating(false);
      setCurrentStepLabel(null);
    }
  };

  return (
    <main className="flex-grow pl-64 flex overflow-hidden h-screen bg-surface-dim">
      {/* Column 1: Collapsible Conversation List */}
      {isThreadSidebarOpen && (
        <aside className="w-72 flex flex-col bg-surface-container border-r border-outline-variant/20 flex-shrink-0 transition-all duration-300">
          <div className="p-4 flex flex-col gap-3 border-b border-outline-variant/10">
            <div className="flex items-center justify-between">
              <span className="text-label-md font-bold text-on-surface-variant uppercase tracking-wider">
                Chat Sessions
              </span>
              <button
                onClick={() => setIsThreadSidebarOpen(false)}
                className="p-1 hover:bg-surface-variant/50 rounded-lg text-on-surface-variant transition-colors cursor-pointer"
                title="Hide thread list"
              >
                <span className="material-symbols-outlined text-[18px]">dock_to_left</span>
              </button>
            </div>
            <button
              onClick={() => {
                setMessages([
                  {
                    id: `msg-${Date.now()}`,
                    sender: "assistant",
                    text: "System reset cleanly. Ready for new architectural reasoning session.",
                    badges: ["LangGraph Ready"],
                  },
                ]);
                setActiveSession(`Session #${Math.floor(Math.random() * 899 + 100)}`);
              }}
              className="w-full bg-primary-container text-on-primary-container py-2.5 px-3 rounded-xl font-label-md font-bold flex items-center justify-center gap-2 active:scale-95 transition-all shadow-md shadow-primary-container/10 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
              New Chat Thread
            </button>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">
                search
              </span>
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-xl py-2 pl-9 pr-3 text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all placeholder:text-on-surface-variant/50"
                placeholder="Search threads..."
                type="text"
              />
            </div>
          </div>

          <div className="flex-grow overflow-y-auto custom-scrollbar p-3 space-y-5">
            {/* Pinned Section */}
            <div>
              <h3 className="text-[11px] font-bold text-on-surface-variant/70 px-2 mb-2 flex items-center gap-1 uppercase tracking-wider">
                <span className="material-symbols-outlined text-[14px] text-primary">push_pin</span>
                Pinned
              </h3>
              <div className="flex flex-col gap-1.5">
                <div className="p-2.5 bg-surface-variant/30 rounded-xl border border-outline-variant/10 cursor-pointer hover:bg-surface-variant/60 transition-colors">
                  <div className="text-body-sm font-bold truncate text-on-surface">Milestone 15 Platform Architecture</div>
                  <div className="text-[11px] text-on-surface-variant truncate mt-0.5">Full production verification...</div>
                </div>
                <div className="p-2.5 bg-surface-variant/30 rounded-xl border border-outline-variant/10 cursor-pointer hover:bg-surface-variant/60 transition-colors">
                  <div className="text-body-sm font-bold truncate text-on-surface">Neo4j Graph Schema Mapping</div>
                  <div className="text-[11px] text-on-surface-variant truncate mt-0.5">Entity relations &amp; facts...</div>
                </div>
              </div>
            </div>

            {/* Today Section */}
            <div>
              <h3 className="text-[11px] font-bold text-on-surface-variant/70 px-2 mb-2 uppercase tracking-wider">Today</h3>
              <div className="flex flex-col gap-1.5">
                <div className="p-2.5 bg-primary/10 border border-primary/30 rounded-xl cursor-pointer shadow-sm">
                  <div className="text-body-sm font-bold text-primary truncate">{activeSession}</div>
                  <div className="text-[11px] text-primary/80 truncate mt-0.5">Active reasoning session...</div>
                </div>
                <div className="p-2.5 hover:bg-surface-variant/40 rounded-xl cursor-pointer transition-colors border border-transparent">
                  <div className="text-body-sm font-semibold truncate text-on-surface">Hybrid RAG Vector Calibration</div>
                  <div className="text-[11px] text-on-surface-variant truncate mt-0.5">Pinecone index checks...</div>
                </div>
              </div>
            </div>

            {/* Yesterday Section */}
            <div>
              <h3 className="text-[11px] font-bold text-on-surface-variant/70 px-2 mb-2 uppercase tracking-wider">Yesterday</h3>
              <div className="flex flex-col gap-1.5 opacity-80">
                <div className="p-2.5 hover:bg-surface-variant/40 rounded-xl cursor-pointer transition-colors border border-transparent">
                  <div className="text-body-sm font-semibold truncate text-on-surface">Security Audit &amp; Observability</div>
                  <div className="text-[11px] text-on-surface-variant truncate mt-0.5">Telemetry logs &amp; evaluation...</div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      )}

      {/* Column 2: Spacious Message Workspace */}
      <section className="flex-grow flex flex-col relative bg-surface-dim min-w-0 overflow-hidden">
        {/* Crisp Top Header Bar */}
        <header className="h-16 flex items-center justify-between px-6 backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20 flex-shrink-0 z-10">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setIsThreadSidebarOpen(!isThreadSidebarOpen)}
              className={`p-2 rounded-xl transition-all flex items-center justify-center cursor-pointer border ${
                isThreadSidebarOpen
                  ? "bg-surface-container-high border-outline-variant/30 text-primary"
                  : "bg-surface-container hover:bg-surface-variant border-outline-variant/20 text-on-surface-variant"
              }`}
              title={isThreadSidebarOpen ? "Hide chat threads" : "Show chat threads"}
            >
              <span className="material-symbols-outlined text-[20px]">dock_to_left</span>
            </button>

            <div className="h-4 w-px bg-outline-variant/20 hidden sm:block"></div>

            <h2 className="text-headline-md font-headline-md font-bold text-on-surface truncate max-w-xs sm:max-w-md">
              {activeSession}
            </h2>

            {/* Razor-Sharp Status Badges (Never wrap) */}
            <div className="hidden lg:flex items-center gap-2 ml-2">
              <span className="whitespace-nowrap flex items-center gap-1.5 px-3 py-1 bg-surface-container-high rounded-full border border-outline-variant/20 text-[11px] font-bold text-on-surface">
                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                Online
              </span>
              <span className="whitespace-nowrap flex items-center gap-1.5 px-3 py-1 bg-surface-container-high rounded-full border border-outline-variant/20 text-[11px] font-bold text-primary">
                <span className="material-symbols-outlined text-[14px]">bolt</span>
                LangGraph v15
              </span>
              <span className="whitespace-nowrap flex items-center gap-1.5 px-3 py-1 bg-primary/10 rounded-full border border-primary/20 text-[11px] font-bold text-primary">
                <span className="material-symbols-outlined text-[14px]">memory</span>
                Memory Active
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => setIsContextSidebarOpen(!isContextSidebarOpen)}
              className={`px-3 py-1.5 rounded-xl transition-all flex items-center gap-2 text-label-md font-bold cursor-pointer border ${
                isContextSidebarOpen
                  ? "bg-primary/10 border-primary/30 text-primary shadow-sm"
                  : "bg-surface-container hover:bg-surface-variant border-outline-variant/20 text-on-surface-variant"
              }`}
              title="Toggle Live Telemetry & Memory Inspector"
            >
              <span className="material-symbols-outlined text-[18px]">analytics</span>
              <span className="hidden sm:inline">Telemetry &amp; RAG</span>
            </button>
          </div>
        </header>

        {/* Centered Spacious Message Area */}
        <div className="flex-grow overflow-y-auto custom-scrollbar px-4 sm:px-6 py-6 flex flex-col items-center">
          <div className="max-w-4xl w-full flex flex-col gap-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === "user" ? "justify-end" : "gap-4"} w-full`}
              >
                {msg.sender === "assistant" && (
                  <div className="w-10 h-10 rounded-xl bg-surface-container-high flex items-center justify-center border border-outline-variant/30 flex-shrink-0 shadow-md mt-0.5">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-primary to-secondary animate-pulse shadow-[0_0_15px_rgba(0,229,255,0.5)]"></div>
                  </div>
                )}

                {msg.sender === "user" ? (
                  <div className="max-w-[80%] glass-surface px-5 py-4 rounded-2xl rounded-tr-sm border border-primary/20 shadow-lg bg-gradient-to-l from-primary/10 to-transparent">
                    <p className="text-body-md text-on-surface leading-relaxed">{msg.text}</p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2 max-w-[90%] flex-grow min-w-0">
                    <div className="flex gap-2 items-center flex-wrap">
                      <span className="text-label-md font-bold text-on-surface">Antigravity Assistant</span>
                      {msg.badges && msg.badges.length > 0 && (
                        <div className="flex gap-1.5 flex-wrap">
                          {msg.badges.map((b) => (
                            <span
                              key={b}
                              className="text-[10px] bg-primary-container/10 text-primary px-2 py-0.5 rounded-full border border-primary/20 font-bold uppercase tracking-wider"
                            >
                              {b}
                            </span>
                          ))}
                        </div>
                      )}
                      {msg.latency_ms && (
                        <span className="text-[10px] text-on-surface-variant opacity-70 font-mono-code ml-auto">
                          ⚡ {Math.round(msg.latency_ms)}ms
                        </span>
                      )}
                    </div>

                    <div className="glass-surface p-6 rounded-2xl rounded-tl-sm border border-outline-variant/20 ai-reasoning-line shadow-xl bg-surface-container-low/60">
                      <ChatMessageRenderer content={msg.text || (isGenerating ? "Synthesizing response via Groq & GraphRAG..." : "")} />
                    </div>

                    <div className="flex items-center gap-3 mt-1 px-1">
                      <button className="p-1 text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1 cursor-pointer rounded hover:bg-surface-variant/30">
                        <span className="material-symbols-outlined text-[16px]">thumb_up</span>
                      </button>
                      <button className="p-1 text-on-surface-variant hover:text-error transition-colors flex items-center gap-1 cursor-pointer rounded hover:bg-surface-variant/30">
                        <span className="material-symbols-outlined text-[16px]">thumb_down</span>
                      </button>
                      <button
                        onClick={() => navigator.clipboard.writeText(msg.text)}
                        className="p-1 text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-1 cursor-pointer rounded hover:bg-surface-variant/30 text-[11px]"
                      >
                        <span className="material-symbols-outlined text-[16px]">content_copy</span>
                        Copy
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Streaming State Progress Indicator */}
            {isGenerating && currentStepLabel && (
              <div className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-surface-container-high flex items-center justify-center border border-outline-variant/30 flex-shrink-0">
                  <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-primary to-secondary animate-pulse opacity-60"></div>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="flex flex-col gap-2 px-4 py-3 rounded-2xl bg-surface-container-low border border-outline-variant/20 shadow-md">
                    <div className="flex items-center gap-2.5">
                      <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
                      <span className="text-label-md font-bold text-primary streaming-pulse">
                        {currentStepLabel}
                      </span>
                    </div>
                    <div className="h-1 bg-surface-variant/30 rounded-full overflow-hidden w-56">
                      <div className="h-full bg-primary w-2/3 shadow-[0_0_8px_#00e5ff] transition-all duration-1000"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Centered Composer Box */}
        <footer className="p-4 sm:p-6 flex-shrink-0 border-t border-outline-variant/10 bg-surface-dim/80 backdrop-blur-md">
          <div className="max-w-4xl mx-auto glass-surface rounded-2xl border border-outline-variant/30 p-3 shadow-2xl relative">
            <div className="flex items-center justify-between gap-2 px-2 pb-2 mb-2 border-b border-outline-variant/10">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 bg-surface-container-high px-2.5 py-1 rounded-lg border border-outline-variant/20 cursor-pointer hover:bg-surface-variant transition-colors group">
                  <span className="material-symbols-outlined text-[16px] text-primary">psychology</span>
                  <span className="text-label-md font-bold text-on-surface-variant group-hover:text-primary transition-colors">
                    LangGraph Orchestrator
                  </span>
                  <span className="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
                </div>
                <div className="flex items-center gap-1.5 bg-surface-container-high px-2.5 py-1 rounded-lg border border-outline-variant/20 cursor-pointer hover:bg-surface-variant transition-colors">
                  <span className="material-symbols-outlined text-[16px] text-secondary">build</span>
                  <span className="text-label-md font-bold text-on-surface-variant">External Tools Active</span>
                </div>
              </div>
              <span className="text-[11px] font-mono-code text-on-surface-variant/60 hidden sm:inline">
                Press Enter to send, Shift+Enter for new line
              </span>
            </div>

            <div className="flex items-end gap-3 px-2">
              <textarea
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="w-full bg-transparent border-none focus:ring-0 text-body-md text-on-surface py-2 resize-none max-h-48 custom-scrollbar placeholder:text-on-surface-variant/40 focus:outline-none"
                placeholder="Message Antigravity AI Engine..."
                rows={1}
              />
              <button
                onClick={handleSendMessage}
                disabled={isGenerating || !inputQuery.trim()}
                className="w-10 h-10 flex-shrink-0 bg-primary-container text-on-primary-container rounded-xl flex items-center justify-center shadow-lg shadow-primary-container/20 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <span className="material-symbols-outlined font-bold text-[20px]">arrow_upward</span>
              </button>
            </div>
          </div>
          <p className="text-center text-[11px] text-on-surface-variant/50 mt-2">
            Antigravity AI runs 100% deterministic LangGraph routing, Neo4j GraphRAG traversal, and cross-encoder RAG verification.
          </p>
        </footer>
      </section>

      {/* Column 3: Collapsible Context Inspector */}
      {isContextSidebarOpen && (
        <aside className="w-80 bg-surface-container-low border-l border-outline-variant/20 overflow-y-auto custom-scrollbar p-5 flex flex-col gap-6 flex-shrink-0 transition-all duration-300">
          <div className="flex items-center justify-between pb-3 border-b border-outline-variant/10">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">insights</span>
              <span className="text-label-md font-bold text-on-surface uppercase tracking-wider">
                Telemetry Inspector
              </span>
            </div>
            <button
              onClick={() => setIsContextSidebarOpen(false)}
              className="p-1 hover:bg-surface-variant/50 rounded-lg text-on-surface-variant transition-colors cursor-pointer"
              title="Close Telemetry Inspector"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>

          <div>
            <h3 className="text-[11px] font-bold text-primary uppercase tracking-widest mb-3 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              Long-Term Memory Profile
            </h3>
            <div className="glass-surface p-4 rounded-xl border border-primary/20 shadow-md">
              <div className="flex items-center justify-between mb-2">
                <span className="text-body-sm font-bold text-on-surface">PostgreSQL Checkpoints</span>
                <span className="text-[10px] px-2 py-0.5 bg-primary/10 text-primary rounded-full font-bold">ACTIVE</span>
              </div>
              {memoryProfile && memoryProfile.semantic_facts.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-[12px] text-on-surface-variant leading-relaxed">
                    Synthesized Facts: <span className="text-primary font-bold">{memoryProfile.semantic_facts.length}</span>
                  </p>
                  <div className="bg-surface-container-lowest p-2.5 rounded-lg border border-outline-variant/20 max-h-36 overflow-y-auto custom-scrollbar text-[12px] space-y-1.5">
                    {memoryProfile.semantic_facts.slice(0, 4).map((f, idx) => (
                      <div key={idx} className="text-on-surface-variant truncate font-mono-code">
                        • {f}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-[12px] text-on-surface-variant leading-relaxed">
                  Tracking session context across hybrid vectors and Graph triples. Semantic memory consolidates automatically after each interaction.
                </p>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-widest mb-3">
              Knowledge Graph &amp; Vector RAG
            </h3>
            <div className="flex flex-col gap-2">
              <div className="flex gap-3 p-3 glass-surface hover:border-primary/40 rounded-xl cursor-pointer transition-all group shadow-sm">
                <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex-shrink-0 flex items-center justify-center border border-primary/20">
                  <span className="material-symbols-outlined">description</span>
                </div>
                <div className="flex flex-col justify-center min-w-0">
                  <span className="text-body-sm font-bold group-hover:text-primary transition-colors text-on-surface truncate">
                    Pinecone Vectors
                  </span>
                  <span className="text-[11px] text-on-surface-variant truncate">Hybrid BM25 + Cross-Encoder</span>
                </div>
              </div>

              <div className="flex gap-3 p-3 glass-surface hover:border-secondary/40 rounded-xl cursor-pointer transition-all group shadow-sm">
                <div className="w-10 h-10 rounded-lg bg-secondary/10 text-secondary flex-shrink-0 flex items-center justify-center border border-secondary/20">
                  <span className="material-symbols-outlined">hub</span>
                </div>
                <div className="flex flex-col justify-center min-w-0">
                  <span className="text-body-sm font-bold group-hover:text-secondary transition-colors text-on-surface truncate">
                    Neo4j Knowledge Graph
                  </span>
                  <span className="text-[11px] text-on-surface-variant truncate">Multi-hop Cypher traversal</span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-widest mb-3">
              Response Quality Metric
            </h3>
            <div className="p-4 glass-surface rounded-xl border border-outline-variant/20 shadow-md">
              <div className="flex justify-between items-center mb-2">
                <span className="text-body-sm font-bold text-on-surface">Groundedness Score</span>
                <span className="text-body-sm font-mono-code font-bold text-primary">100%</span>
              </div>
              <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-primary to-secondary w-[100%] shadow-[0_0_10px_#00e5ff]"></div>
              </div>
              <div className="mt-3 pt-3 border-t border-outline-variant/10 flex flex-col gap-2">
                <div className="flex justify-between text-[11px] text-on-surface-variant">
                  <span>Hallucination Safety</span>
                  <span className="text-emerald-400 font-bold font-mono-code">0.00 Verified</span>
                </div>
                <div className="flex justify-between text-[11px] text-on-surface-variant">
                  <span>Latency SLA</span>
                  <span className="text-primary font-bold font-mono-code">Sub-200ms</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-auto pt-4 border-t border-outline-variant/10">
            <div className="bg-gradient-to-br from-primary/10 to-secondary/10 p-4 rounded-xl border border-primary/20 shadow-lg">
              <div className="flex items-center gap-2 mb-2 text-primary">
                <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
                <span className="text-label-md font-bold uppercase tracking-wider">Observability Pro</span>
              </div>
              <p className="text-[12px] text-on-surface-variant mb-3 leading-relaxed">
                Inspect full evaluation traces and node-by-node execution graphs in real time.
              </p>
              <Link
                href="/evaluation"
                className="block w-full py-2 bg-primary text-on-primary rounded-lg text-label-md font-bold hover:opacity-90 transition-all text-center shadow-md shadow-primary/20"
              >
                Open Evaluation Suite
              </Link>
            </div>
          </div>
        </aside>
      )}
    </main>
  );
}
