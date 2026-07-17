"use client";

import React, { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

interface MemoryEntry {
  id: string;
  type: "fact" | "preference" | "episode";
  content: string;
  created_at: string;
}

export default function MemoryPage() {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/memory/profile?user_id=test-user`)
      .then((res) => (res.ok ? res.json() : Promise.reject("No backend")))
      .then((data) => {
        const facts: MemoryEntry[] = (data.semantic_facts || []).map((f: any, i: number) => ({
          id: `fact-${i}`,
          type: "fact" as const,
          content: f.fact || f.content || "",
          created_at: f.created_at || "",
        }));
        const prefs: MemoryEntry[] = (data.preferences || []).map((p: any, i: number) => ({
          id: `pref-${i}`,
          type: "preference" as const,
          content: p.preference || p.content || "",
          created_at: p.created_at || "",
        }));
        const episodes: MemoryEntry[] = (data.episodes || []).map((e: any, i: number) => ({
          id: `ep-${i}`,
          type: "episode" as const,
          content: e.summary || e.content || "",
          created_at: e.created_at || "",
        }));
        setEntries([...facts, ...prefs, ...episodes]);
      })
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>memory</span>
          </div>
          <div>
            <h2 className="text-[22px] font-bold text-on-surface leading-tight">Long-Term Memory</h2>
            <p className="text-[12px] text-on-surface-variant">User Profile, Semantic Facts &amp; Episodes</p>
          </div>
        </div>

        <div className="glass-card p-8 rounded-2xl border border-outline-variant/20">
          <h3 className="text-[16px] font-bold text-on-surface mb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">history_edu</span>
            Recent Memory Entries
          </h3>
          <p className="text-[13px] text-on-surface-variant mb-6">
            Your assistant remembers preferences and context across conversations for a personalized experience.
          </p>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-on-surface-variant text-4xl mb-3 block">psychology</span>
              <p className="text-[13px] text-on-surface-variant">No memory entries yet. Memories are created automatically as you interact with the assistant.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {entries.map((entry) => (
                <div key={entry.id} className="flex items-start gap-3 p-4 rounded-xl bg-surface-container-high border border-outline-variant/10">
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5 ${
                    entry.type === "preference"
                      ? "bg-secondary/20 text-secondary border border-secondary/30"
                      : entry.type === "fact"
                      ? "bg-tertiary/20 text-tertiary border border-tertiary/30"
                      : "bg-primary/20 text-primary border border-primary/30"
                  }`}>
                    {entry.type.charAt(0).toUpperCase() + entry.type.slice(1)}
                  </span>
                  <p className="text-[13px] text-on-surface flex-1">{entry.content}</p>
                  {entry.created_at && (
                    <span className="text-[11px] text-on-surface-variant font-mono flex-shrink-0">{new Date(entry.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
