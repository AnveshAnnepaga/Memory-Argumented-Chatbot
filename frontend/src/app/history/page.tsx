"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useChatStore, Conversation } from "../../store/useChatStore";

export default function HistoryPage() {
  const router = useRouter();
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    createConversation,
    deleteConversation,
    renameConversation,
    togglePinConversation,
  } = useChatStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const filtered = conversations.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pinned = filtered.filter((c) => c.pinned);
  const unpinned = filtered.filter((c) => !c.pinned);

  const handleCreateNew = () => {
    createConversation("New Intelligence Session");
    router.push("/chat");
  };

  const handleSelectSession = (id: string) => {
    setActiveConversationId(id);
    router.push("/chat");
  };

  const startRename = (c: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(c.id);
    setEditTitle(c.title);
  };

  const saveRename = (id: string, e: React.MouseEvent | React.FormEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      renameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <main className="ml-64 pt-16 min-h-screen bg-background text-on-surface pb-24">
      {/* Top Header Bar */}
      <header className="fixed top-0 left-64 right-0 z-50 h-16 flex justify-between items-center px-lg backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[24px]">history</span>
          <h2 className="text-headline-md font-headline-md font-bold text-on-surface">Intelligence Session Archive</h2>
        </div>
        <div className="flex items-center gap-md">
          <span className="text-label-md px-3 py-1 bg-primary-container/10 text-primary border border-primary/20 rounded-full font-bold uppercase">
            PostgreSQL Checkpointed
          </span>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            notifications
          </button>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            contrast
          </button>
        </div>
      </header>

      <div className="p-lg max-w-6xl mx-auto space-y-lg">
        {/* Top Banner & Search */}
        <div className="glass-surface p-lg rounded-2xl border border-outline-variant/20 flex flex-col md:flex-row md:items-center justify-between gap-md shadow-xl">
          <div className="space-y-1">
            <h1 className="text-headline-lg font-headline-lg font-bold text-on-surface">LangGraph Orchestration Logs</h1>
            <p className="text-body-sm text-on-surface-variant">
              Review persistent reasoning chains, state graph checkpoints, and retrieved memory episodes across all past sessions.
            </p>
          </div>
          <div className="flex items-center gap-md">
            <div className="relative w-full md:w-80">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
                search
              </span>
              <input
                type="text"
                placeholder="Search session archive by query or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-surface-container-highest border border-outline-variant/20 rounded-xl pl-10 pr-4 py-2.5 text-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40"
              />
            </div>
            <button
              onClick={handleCreateNew}
              className="px-5 py-2.5 rounded-xl bg-primary-container text-on-primary-container font-bold shadow-lg hover:opacity-90 transition-all flex items-center gap-2 cursor-pointer flex-shrink-0"
            >
              <span className="material-symbols-outlined text-[20px]">add</span>
              New Session
            </button>
          </div>
        </div>

        {/* Pinned Sessions Section */}
        {pinned.length > 0 && (
          <div className="space-y-md">
            <div className="flex items-center gap-2 text-primary font-bold text-label-md uppercase tracking-wider">
              <span className="material-symbols-outlined text-[18px]">push_pin</span>
              Pinned Intelligence Sessions
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
              {pinned.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleSelectSession(c.id)}
                  className={`glass-surface p-md rounded-xl border transition-all cursor-pointer group hover:scale-[1.01] shadow-md flex flex-col justify-between ${
                    c.id === activeConversationId ? "border-primary bg-surface-container-high" : "border-outline-variant/20"
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono-code text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20 font-bold">
                        PINNED • {c.id.slice(0, 8)}
                      </span>
                      <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            togglePinConversation(c.id);
                          }}
                          className="p-1 hover:text-primary transition-colors cursor-pointer"
                          title="Unpin session"
                        >
                          <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                            push_pin
                          </span>
                        </button>
                        <button
                          onClick={(e) => startRename(c, e)}
                          className="p-1 hover:text-secondary transition-colors cursor-pointer"
                          title="Rename"
                        >
                          <span className="material-symbols-outlined text-[18px]">edit</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm("Delete this conversation session?")) deleteConversation(c.id);
                          }}
                          className="p-1 hover:text-error transition-colors cursor-pointer"
                          title="Delete"
                        >
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </div>

                    {editingId === c.id ? (
                      <div className="flex items-center gap-2 mt-1" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          className="bg-surface-container border border-primary rounded-lg px-2 py-1 text-body-sm text-on-surface w-full focus:outline-none"
                          autoFocus
                        />
                        <button onClick={(e) => saveRename(c.id, e)} className="p-1 text-tertiary font-bold cursor-pointer">
                          <span className="material-symbols-outlined text-[18px]">check</span>
                        </button>
                      </div>
                    ) : (
                      <h3 className="text-body-md font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">
                        {c.title}
                      </h3>
                    )}
                  </div>

                  <div className="pt-4 mt-4 border-t border-outline-variant/10 flex items-center justify-between text-label-md text-on-surface-variant opacity-70">
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">calendar_today</span>
                      {new Date(c.createdAt).toLocaleDateString()}
                    </span>
                    <span>LangGraph Engine</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Sessions Table */}
        <div className="space-y-md">
          <div className="flex items-center justify-between">
            <h3 className="text-headline-md font-headline-md font-bold text-on-surface">All Recorded Sessions</h3>
            <span className="text-label-md text-on-surface-variant">Showing {filtered.length} total sessions</span>
          </div>

          {filtered.length === 0 ? (
            <div className="glass-surface p-12 rounded-2xl border border-dashed border-outline-variant/30 text-center space-y-3">
              <span className="material-symbols-outlined text-[48px] text-on-surface-variant/40">history</span>
              <p className="text-body-md text-on-surface-variant">No archived sessions match your filter.</p>
              <button
                onClick={handleCreateNew}
                className="px-4 py-2 bg-primary-container text-on-primary-container rounded-xl font-bold text-label-md cursor-pointer"
              >
                Start First Session
              </button>
            </div>
          ) : (
            <div className="glass-surface rounded-2xl border border-outline-variant/20 overflow-hidden shadow-xl">
              <table className="w-full text-left border-collapse">
                <thead className="bg-surface-container-high/60 border-b border-outline-variant/10">
                  <tr>
                    <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                      Session Title
                    </th>
                    <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                      Session ID
                    </th>
                    <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                      Orchestration Status
                    </th>
                    <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10">
                  {unpinned.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => handleSelectSession(c.id)}
                      className={`hover:bg-surface-variant/20 transition-colors cursor-pointer group ${
                        c.id === activeConversationId ? "bg-primary/5" : ""
                      }`}
                    >
                      <td className="px-lg py-4">
                        {editingId === c.id ? (
                          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              className="bg-surface-container border border-primary rounded-lg px-3 py-1 text-body-sm text-on-surface focus:outline-none w-64"
                              autoFocus
                            />
                            <button onClick={(e) => saveRename(c.id, e)} className="p-1 text-tertiary font-bold cursor-pointer">
                              <span className="material-symbols-outlined text-[18px]">check</span>
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-surface-container-high text-primary group-hover:bg-primary/10 transition-colors">
                              <span className="material-symbols-outlined text-[20px]">chat_bubble</span>
                            </div>
                            <span className="text-body-sm font-bold text-on-surface group-hover:text-primary transition-colors">
                              {c.title}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-lg py-4 text-body-sm font-mono-code text-on-surface-variant opacity-70">
                        {c.id.slice(0, 16)}...
                      </td>
                      <td className="px-lg py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-tertiary/10 text-tertiary border border-tertiary/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                          Checkpointed
                        </span>
                      </td>
                      <td className="px-lg py-4 text-body-sm text-on-surface-variant">
                        {new Date(c.createdAt).toLocaleString()}
                      </td>
                      <td className="px-lg py-4 text-right">
                        <div className="flex justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              togglePinConversation(c.id);
                            }}
                            className="p-1.5 hover:text-primary transition-colors cursor-pointer"
                            title="Pin session"
                          >
                            <span className="material-symbols-outlined text-[18px]">push_pin</span>
                          </button>
                          <button
                            onClick={(e) => startRename(c, e)}
                            className="p-1.5 hover:text-secondary transition-colors cursor-pointer"
                            title="Rename"
                          >
                            <span className="material-symbols-outlined text-[18px]">edit</span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm("Delete this conversation session?")) deleteConversation(c.id);
                            }}
                            className="p-1.5 hover:text-error transition-colors cursor-pointer"
                            title="Delete"
                          >
                            <span className="material-symbols-outlined text-[18px]">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
