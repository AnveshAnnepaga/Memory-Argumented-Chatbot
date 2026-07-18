"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAppStore } from "@/store/useAppStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

interface ConversationSummary {
  id: string;
  title: string;
  preview: string;
  date: string;
  msgs: number;
}

export default function HistoryPage() {
  const { token, conversationSaveCount } = useAppStore();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const handleDelete = async (e: React.MouseEvent, cid: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/chat/conversations/${encodeURIComponent(cid)}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== cid));
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetch(`${API_BASE_URL}/chat/conversations`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject("No backend")))
      .then((data) => {
        const items: ConversationSummary[] = (data.data || []).map((c: any) => ({
          id: c.id,
          title: c.title || "Untitled",
          preview: c.last_message || "",
          date: c.updated_at || "",
          msgs: c.message_count || 0,
        }));
        setConversations(items);
      })
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, [token, conversationSaveCount]);

  const filtered = conversations.filter(
    (h) =>
      h.title.toLowerCase().includes(search.toLowerCase()) ||
      h.preview.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>history</span>
          </div>
          <div>
            <h2 className="text-[22px] font-bold text-on-surface leading-tight">Conversation History</h2>
            <p className="text-[12px] text-on-surface-variant font-mono">Browse, search, and revisit past sessions</p>
          </div>
        </div>

        <div className="glass-surface rounded-xl border border-outline-variant/20 flex items-center gap-3 px-4 py-3 shadow-lg">
          <span className="material-symbols-outlined text-on-surface-variant text-[20px]">search</span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations..."
            className="flex-1 bg-transparent border-none focus:outline-none text-body-md text-on-surface placeholder:text-on-surface-variant/40"
          />
          {search && (
            <button onClick={() => setSearch("")} className="text-on-surface-variant hover:text-on-surface transition-colors">
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          )}
        </div>

        <div className="flex flex-col gap-3">
          {loading ? (
            <div className="glass-card p-10 rounded-2xl border border-outline-variant/20 text-center">
              <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-3"></div>
              <p className="text-body-md text-on-surface-variant">Loading conversations...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="glass-card p-10 rounded-2xl border border-outline-variant/20 text-center">
              <span className="material-symbols-outlined text-on-surface-variant text-5xl mb-3 block">forum</span>
              <p className="text-body-md text-on-surface-variant">
                {search ? "No conversations match your search." : "No past conversations yet. Start a chat to see your history here."}
              </p>
            </div>
          ) : (
            filtered.map((h) => (
              <Link
                key={h.id}
                href={`/chat?conversation=${encodeURIComponent(h.id)}`}
                className="glass-card px-5 py-4 rounded-xl border border-outline-variant/20 flex items-start gap-4 cursor-pointer hover:border-primary/30 transition-all group"
              >
                <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="material-symbols-outlined text-on-surface-variant text-[18px]">forum</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[14px] font-semibold text-on-surface truncate group-hover:text-primary transition-colors">{h.title}</p>
                    {h.date && <span className="text-[11px] font-mono text-on-surface-variant flex-shrink-0">{h.date}</span>}
                  </div>
                  <p className="text-[13px] text-on-surface-variant mt-0.5 truncate">{h.preview}</p>
                  <p className="text-[11px] font-mono text-on-surface-variant/50 mt-1">{h.msgs} messages</p>
                </div>
                <button
                  onClick={(e) => handleDelete(e, h.id)}
                  className="p-1.5 rounded-lg hover:bg-error/20 text-on-surface-variant/30 hover:text-error transition-all flex-shrink-0 mt-0.5 cursor-pointer"
                  title="Delete conversation"
                >
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                </button>
                <span className="material-symbols-outlined text-on-surface-variant/30 group-hover:text-primary/60 transition-colors text-[18px] flex-shrink-0 mt-1">chevron_right</span>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
