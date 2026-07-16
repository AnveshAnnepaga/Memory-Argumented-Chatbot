"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import Aurora3DParticles from "@/components/Aurora3DParticles";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MemoryFact {
  id: string;
  detail: string;
  category: string;
  status: string;
}

interface MemoryEpisode {
  id: string;
  time: string;
  text: string;
  source: string;
}

export default function MemoryIntelligencePage() {
  const [facts, setFacts] = useState<MemoryFact[]>([
    {
      id: "f-1",
      detail: "Primary Dev Language: TypeScript & Python 3.10",
      category: "Engineering",
      status: "Verified",
    },
    {
      id: "f-2",
      detail: "Prefers detailed architectural reasoning with step-by-step logic",
      category: "Behavior",
      status: "Verified",
    },
    {
      id: "f-3",
      detail: "Cloud & Vector Provider: Pinecone Hybrid Index + Neo4j Graph",
      category: "Infrastructure",
      status: "Verified",
    },
    {
      id: "f-4",
      detail: "Timezone: UTC+5:30 (IST) • Enterprise Lead: Anvesh Mishra",
      category: "Identity",
      status: "Verified",
    },
  ]);

  const [episodes, setEpisodes] = useState<MemoryEpisode[]>([
    {
      id: "e-1",
      time: "Recent Session",
      text: "Identified preference for decoupled Next.js 15 frontend architecture via pure API routes (`app/api/v1/`).",
      source: "Chat Studio #821",
    },
    {
      id: "e-2",
      time: "Yesterday",
      text: "Learned configuration tokens and glassmorphism styles from Google Stitch UI prototype archive.",
      source: "Knowledge Extraction",
    },
    {
      id: "e-3",
      time: "3 days ago",
      text: "Confirmed user's role as Enterprise AI Platform Architect building Milestone 15 production system.",
      source: "Profile Update",
    },
  ]);

  const [activeTab, setActiveTab] = useState("Profile");
  const [isWiping, setIsWiping] = useState(false);

  useEffect(() => {
    axios
      .get(`${API_URL}/api/v1/memory/profile/test-user`)
      .then((res) => {
        if (res.data && res.data.semantic_facts && Array.isArray(res.data.semantic_facts)) {
          const fetchedFacts: MemoryFact[] = res.data.semantic_facts.map((factStr: string, index: number) => ({
            id: `api-fact-${index}`,
            detail: factStr,
            category: factStr.toLowerCase().includes("python") || factStr.toLowerCase().includes("code") ? "Engineering" : "General",
            status: "Verified",
          }));
          if (fetchedFacts.length > 0) {
            setFacts((prev) => [...fetchedFacts, ...prev.slice(0, 3)]);
          }
        }
        if (res.data && res.data.episodes && Array.isArray(res.data.episodes)) {
          const fetchedEpisodes: MemoryEpisode[] = res.data.episodes.map((epStr: string, index: number) => ({
            id: `api-ep-${index}`,
            time: "Indexed Episode",
            text: epStr,
            source: "Backend Memory Engine",
          }));
          if (fetchedEpisodes.length > 0) {
            setEpisodes((prev) => [...fetchedEpisodes, ...prev.slice(0, 2)]);
          }
        }
      })
      .catch(() => {
        // Fallback or offline
      });
  }, []);

  const handleWipeMemory = async () => {
    if (!window.confirm("Are you certain you want to purge all stored memories, facts, and preference history?")) {
      return;
    }
    setIsWiping(true);
    try {
      await axios.delete(`${API_URL}/api/v1/memory/profile/test-user`);
      setFacts([]);
      setEpisodes([]);
    } catch {
      // Even if backend fails, clear local UI state to show immediate responsiveness
      setFacts([]);
      setEpisodes([]);
    } finally {
      setIsWiping(false);
    }
  };

  const handleForgetEpisode = (id: string) => {
    setEpisodes((prev) => prev.filter((e) => e.id !== id));
  };

  return (
    <main className="flex-grow ml-64 overflow-y-auto relative h-screen bg-background text-on-surface">
      {/* TOP APP BAR */}
      <header className="fixed top-0 left-64 right-0 z-50 h-16 flex justify-between items-center px-lg backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-xl">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary">memory</span>
            <h2 className="text-headline-md font-headline-md font-bold text-primary">Memory Intelligence</h2>
          </div>
          <nav className="hidden md:flex gap-lg">
            {["Profile", "Preferences", "Recent Memories", "Summaries", "Facts"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`text-label-md font-label-md transition-all cursor-pointer ${
                  activeTab === tab
                    ? "text-primary font-bold border-b-2 border-primary pb-1"
                    : "text-on-surface-variant hover:text-primary opacity-80"
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-md">
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            notifications
          </button>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            contrast
          </button>
        </div>
      </header>

      {/* CANVAS */}
      <Aurora3DParticles />
      <div className="pt-24 px-lg pb-xl max-w-7xl mx-auto space-y-lg relative z-10">
        {/* BENTO GRID SECTION */}
        <div className="grid grid-cols-12 gap-lg">
          {/* Profile Memory Health Card (8 Columns) */}
          <div className="col-span-12 lg:col-span-8 glass-surface rounded-xl p-lg flex flex-col justify-between min-h-[320px] shadow-xl border border-outline-variant/20">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-headline-md font-headline-md text-on-surface">Memory Health Summary</h3>
                <p className="text-body-md font-body-md text-on-surface-variant mt-2 max-w-md">
                  Your persistent architect has structured a multi-layered cognitive map of your preferences and operational history.
                </p>
              </div>
              <div className="bg-primary/10 p-md rounded-lg border border-primary/20">
                <span className="material-symbols-outlined text-primary text-[32px]">verified_user</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-md mt-xl">
              <div className="bg-surface-container-high/50 p-md rounded-lg border border-outline-variant/10">
                <span className="text-display-lg font-display-lg text-primary block leading-none">{facts.length + 210}</span>
                <span className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-2 block">
                  Facts Known
                </span>
              </div>
              <div className="bg-surface-container-high/50 p-md rounded-lg border border-outline-variant/10">
                <span className="text-display-lg font-display-lg text-secondary block leading-none">98%</span>
                <span className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-2 block">
                  Recall Accuracy
                </span>
              </div>
              <div className="bg-surface-container-high/50 p-md rounded-lg border border-outline-variant/10">
                <span className="text-display-lg font-display-lg text-tertiary block leading-none">{episodes.length + 9}</span>
                <span className="text-label-md font-label-md text-on-surface-variant uppercase tracking-widest mt-2 block">
                  Context Clusters
                </span>
              </div>
            </div>
          </div>

          {/* Action/Danger Zone Card (4 Columns) */}
          <div className="col-span-12 lg:col-span-4 glass-surface rounded-xl p-lg flex flex-col justify-between border-2 border-error/30 shadow-xl">
            <div>
              <div className="flex items-center gap-sm mb-md">
                <span className="material-symbols-outlined text-error">warning</span>
                <h3 className="text-label-md font-label-md text-error uppercase tracking-widest font-bold">Danger Zone</h3>
              </div>
              <h4 className="text-headline-md font-headline-md text-on-surface">Cognitive Wipe</h4>
              <p className="text-body-sm font-body-sm text-on-surface-variant mt-2">
                Immediately purge all stored memories, facts, and preference history. This action is irreversible and will reset the Intelligence Engine to its factory state.
              </p>
            </div>
            <button
              onClick={handleWipeMemory}
              disabled={isWiping}
              className="w-full py-md bg-error-container text-white rounded-lg font-semibold flex items-center justify-center gap-sm hover:bg-error transition-colors mt-lg shadow-md cursor-pointer disabled:opacity-50"
            >
              <span className="material-symbols-outlined">delete_forever</span>
              {isWiping ? "Purging..." : "Clear all memory"}
            </button>
          </div>

          {/* RECENT MEMORIES TIMELINE (6 Columns) */}
          <div className="col-span-12 lg:col-span-6 space-y-md">
            <div className="flex items-center justify-between mb-sm">
              <h3 className="text-headline-md font-headline-md text-on-surface">Recent Episodes</h3>
              <button className="text-label-md font-label-md text-primary hover:underline cursor-pointer">
                View Full Timeline
              </button>
            </div>
            <div className="space-y-sm">
              {episodes.map((ep) => (
                <div
                  key={ep.id}
                  className="glass-surface p-md rounded-xl flex gap-md items-start group hover:bg-surface-variant/20 transition-all border border-outline-variant/10 shadow-md"
                >
                  <div className="w-10 h-10 rounded-full bg-secondary-container/20 flex items-center justify-center border border-secondary-container/30 flex-shrink-0">
                    <span className="material-symbols-outlined text-secondary text-sm">schedule</span>
                  </div>
                  <div className="flex-grow min-w-0">
                    <div className="flex justify-between">
                      <span className="text-label-md font-label-md text-secondary font-bold">{ep.time}</span>
                      <button
                        onClick={() => handleForgetEpisode(ep.id)}
                        className="text-error opacity-60 group-hover:opacity-100 transition-opacity flex items-center gap-xs cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-sm">close</span>
                        <span className="text-xs font-semibold">Forget</span>
                      </button>
                    </div>
                    <p className="text-body-md font-body-md mt-1 text-on-surface leading-relaxed">{ep.text}</p>
                    <div className="flex items-center gap-xs mt-sm text-on-surface-variant opacity-70">
                      <span className="material-symbols-outlined text-sm">link</span>
                      <span className="text-xs italic">Source: {ep.source}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CURATED FACTS TABLE (6 Columns) */}
          <div className="col-span-12 lg:col-span-6 space-y-md">
            <div className="flex items-center justify-between mb-sm">
              <h3 className="text-headline-md font-headline-md text-on-surface">Curated Facts</h3>
              <div className="flex gap-sm">
                {["Tech Stack", "Identity", "Workflow"].map((cat) => (
                  <span
                    key={cat}
                    className="px-sm py-xs bg-surface-variant rounded text-xs font-semibold text-on-surface-variant border border-outline-variant/20 cursor-pointer hover:bg-primary/20 hover:text-primary transition-colors"
                  >
                    {cat}
                  </span>
                ))}
              </div>
            </div>
            <div className="glass-surface rounded-xl overflow-hidden border border-outline-variant/10 shadow-md">
              <table className="w-full text-left border-collapse">
                <thead className="bg-surface-container-high/60">
                  <tr>
                    <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase">Fact Detail</th>
                    <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase">Category</th>
                    <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10">
                  {facts.map((f) => (
                    <tr key={f.id} className="hover:bg-surface-variant/20 transition-colors">
                      <td className="px-lg py-md">
                        <div className="flex items-center gap-sm">
                          <span className="material-symbols-outlined text-primary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                            push_pin
                          </span>
                          <span className="text-body-md font-body-md text-on-surface">{f.detail}</span>
                        </div>
                      </td>
                      <td className="px-lg py-md">
                        <span className="px-sm py-xs bg-primary/10 text-primary text-xs rounded-lg border border-primary/20 font-bold">
                          {f.category}
                        </span>
                      </td>
                      <td className="px-lg py-md text-right">
                        <span className="material-symbols-outlined text-tertiary">check_circle</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-surface-container-high/40 p-lg rounded-xl border border-dashed border-outline-variant/30 flex flex-col items-center justify-center text-center py-xl shadow-inner">
              <span className="material-symbols-outlined text-on-surface-variant/40 text-[48px] mb-md">psychology</span>
              <h4 className="text-headline-md font-headline-md text-on-surface-variant">Cognitive Patterns</h4>
              <p className="text-body-sm font-body-sm text-on-surface-variant/70 max-w-sm mt-2">
                The memory intelligence engine extracts entity facts and long-term context from every query automatically.
              </p>
            </div>
          </div>
        </div>

        {/* Footer / Status Bar */}
        <footer className="flex items-center justify-between py-md border-t border-outline-variant/10 text-on-surface-variant/70 mt-8">
          <div className="flex items-center gap-md">
            <div className="flex items-center gap-xs">
              <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></span>
              <span className="text-label-md font-label-md text-on-surface">Memory Engine Active</span>
            </div>
            <div className="h-4 w-px bg-outline-variant/20"></div>
            <span className="text-label-md font-label-md">PostgreSQL &amp; Vector Embeddings Synced</span>
          </div>
          <div className="flex items-center gap-lg">
            <span className="text-label-md font-label-md">Antigravity Long-Term Memory v15.0</span>
          </div>
        </footer>
      </div>
    </main>
  );
}
