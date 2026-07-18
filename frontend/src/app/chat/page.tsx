"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import axios from "axios";
import ChatMessageRenderer from "@/components/ChatMessageRenderer";
import FileUploader from "@/components/FileUploader";
import AttachmentRenderer from "@/components/AttachmentRenderer";
import { useAppStore } from "@/store/useAppStore";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}

interface UploadedFileInfo {
  fileId: string;
  filename: string;
  type: 'pdf' | 'docx' | 'image' | 'other';
  uploading: boolean;
  error?: string;
}

interface ConversationSummary {
  id: string;
  title: string;
  last_message: string;
  updated_at: string;
  message_count: number;
}

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  attachments?: UploadedFileInfo[];
}

export default function ChatStudioPage() {
  const searchParams = useSearchParams();
  const { token, authUser, conversationSaveCount, incrementConversationSaveCount } = useAppStore();
  const [conversationId, setConversationId] = useState(searchParams.get("conversation") || generateSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: "Hi! I'm Vyron AI — your assistant. Ask me anything: coding, analysis, explanations, or just a quick chat. You can also upload PDF, DOCX, or images for me to process.",
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStepLabel, setCurrentStepLabel] = useState<string | null>(null);
  const [isThreadSidebarOpen, setIsThreadSidebarOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [showFileUploader, setShowFileUploader] = useState(false);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pendingSendRef = useRef<UploadedFileInfo[] | null>(null);
  const sendMessageRef = useRef<((opts?: { text?: string; files?: UploadedFileInfo[] }) => Promise<void>) | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentStepLabel]);

  const loadedConversationRef = useRef<string | null>(null);
  useEffect(() => {
    const cid = searchParams.get("conversation");
    if (!cid || !token) return;
    if (loadedConversationRef.current === cid) return;
    loadedConversationRef.current = cid;
    setConversationId(cid);
    fetch(`${API_URL}/api/v1/chat/conversations/${encodeURIComponent(cid)}/messages`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.data) {
          setMessages([
            {
              id: "welcome",
              sender: "assistant",
              text: "Hi! I'm Vyron AI — your assistant.",
            },
            ...data.data.map((m: { id: string; sender: string; text: string }) => ({
              id: m.id,
              sender: m.sender as "user" | "assistant",
              text: m.text,
            })),
          ]);
        }
      })
      .catch(() => {});
  }, [token, searchParams]);

  const fetchConversations = useCallback(async () => {
    if (!token) return;
    setConversationsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data.data || []);
      }
    } catch {
      // ignore
    } finally {
      setConversationsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations, conversationSaveCount]);

  const handleDeleteConversation = useCallback(async (cid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/chat/conversations/${encodeURIComponent(cid)}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== cid));
      }
    } catch {
      // ignore
    }
  }, [token]);

  useEffect(() => {
    if (pendingSendRef.current && sendMessageRef.current) {
      const files = pendingSendRef.current;
      pendingSendRef.current = null;
      sendMessageRef.current({ files });
    }
  }, [uploadedFiles]);

  const handleFilesUploaded = useCallback((files: UploadedFileInfo[]) => {
    setUploadedFiles((prev) => [...prev, ...files]);
    pendingSendRef.current = files;
    setTimeout(() => setShowFileUploader(false), 500);
  }, []);

  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.fileId !== fileId));
  }, []);

  const handleSendMessage = async (opts?: { text?: string; files?: UploadedFileInfo[] }) => {
    const text = opts?.text ?? inputQuery.trim();
    const files = opts?.files ?? uploadedFiles;
    if ((!text && files.length === 0) || isGenerating) return;

    const userText = text;
    if (!opts) setInputQuery("");
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;

    const attachments = files.length > 0 ? [...files] : undefined;
    const fileIds = files.filter(f => f.type !== 'image').map(f => f.fileId);
    const imageIds = files.filter(f => f.type === 'image').map(f => f.fileId);

    setUploadedFiles([]);

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: "user", text: userText, attachments },
      { id: assistantMsgId, sender: "assistant", text: "" },
    ]);

    setIsGenerating(true);
    setCurrentStepLabel("Thinking...");

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          query: userText,
          user_id: authUser?.id || "default",
          conversation_id: conversationId,
          file_ids: fileIds,
          image_ids: imageIds,
        }),
      });

      if (!response.body) {
        throw new Error("No readable stream received.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

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
              setCurrentStepLabel(parsed.label || "Processing...");
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
          } else if (eventType === "complete" || eventType === "done") {
            setCurrentStepLabel(null);
          }
        }
      }
    } catch {
      try {
        const res = await axios.post(`${API_URL}/api/v1/chat/query`, {
          query: userText,
          user_id: authUser?.id || "default",
          conversation_id: conversationId,
          file_ids: fileIds,
          image_ids: imageIds,
        }, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
        const d = res.data?.data || res.data || {};
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, text: d.response || "" }
              : m
          )
        );
      } catch {
        // silently fail — no error shown in chat bubble
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, text: "" }
              : m
          )
        );
      }
    } finally {
      setIsGenerating(false);
      setCurrentStepLabel(null);
    }
  };

  sendMessageRef.current = handleSendMessage;

  return (
    <main className="flex flex-1 overflow-hidden h-full bg-surface-dim">
      {isThreadSidebarOpen && (
        <aside className="w-72 flex flex-col bg-surface-container border-r border-outline-variant/20 flex-shrink-0 transition-all duration-300">
          <div className="p-4 flex flex-col gap-3 border-b border-outline-variant/10">
            <div className="flex items-center justify-between">
              <span className="text-label-md font-bold text-on-surface-variant uppercase tracking-wider">
                Conversations
              </span>
              <button
                onClick={() => setIsThreadSidebarOpen(false)}
                className="p-1 hover:bg-surface-variant/50 rounded-lg text-on-surface-variant transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">dock_to_left</span>
              </button>
            </div>
            <button
              onClick={() => {
                setConversationId(generateSessionId());
                setMessages([
                  {
                    id: `msg-${Date.now()}`,
                    sender: "assistant",
                    text: "Ready for a new conversation.",
                  },
                ]);
                setUploadedFiles([]);
              }}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-primary-container/20 text-primary text-[14px] font-semibold hover:bg-primary-container/40 transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">add_circle</span>
              New Conversation
            </button>
          </div>
          <div className="flex-grow overflow-y-auto custom-scrollbar px-2 py-2">
            {conversationsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
              </div>
            ) : conversations.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-body-sm text-on-surface-variant">No past conversations</p>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => {
                      window.location.href = `/chat?conversation=${encodeURIComponent(conv.id)}`;
                    }}
                    className="group flex items-center gap-2 px-3 py-2.5 rounded-xl hover:bg-surface-variant/50 transition-colors cursor-pointer"
                  >
                    <div className="flex-grow min-w-0">
                      <p className="text-label-md font-semibold text-on-surface truncate">
                        {conv.title}
                      </p>
                      <p className="text-body-xs text-on-surface-variant truncate">
                        {conv.message_count} messages
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="p-1.5 rounded-lg hover:bg-error/20 text-on-surface-variant hover:text-error transition-all cursor-pointer flex-shrink-0"
                      title="Delete conversation"
                    >
                      <span className="material-symbols-outlined text-[16px]">delete</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>
      )}

      <section className="flex-grow flex flex-col relative bg-surface-dim min-w-0 overflow-hidden">
        <header className="h-16 flex items-center justify-between px-6 backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20 flex-shrink-0 z-10">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setIsThreadSidebarOpen(!isThreadSidebarOpen)}
              className={`p-2 rounded-xl transition-all flex items-center justify-center cursor-pointer border ${
                isThreadSidebarOpen
                  ? "bg-surface-container-high border-outline-variant/30 text-primary"
                  : "bg-surface-container hover:bg-surface-variant border-outline-variant/20 text-on-surface-variant"
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">dock_to_left</span>
            </button>
            <div className="h-4 w-px bg-outline-variant/20 hidden sm:block"></div>
            <h2 className="text-headline-md font-headline-md font-bold text-on-surface truncate max-w-xs sm:max-w-md">
              Chat
            </h2>
          </div>
          <div className="flex items-center gap-2">
            {saveMsg && (
              <span className="text-[11px] font-mono text-tertiary animate-pulse">{saveMsg}</span>
            )}
            <button
              onClick={() => {
                setConversationId(generateSessionId());
                setMessages([{
                  id: `msg-${Date.now()}`,
                  sender: "assistant",
                  text: "Ready for a new conversation.",
                }]);
                setUploadedFiles([]);
              }}
              className="px-3 py-1.5 rounded-xl bg-secondary-container/20 text-secondary text-[12px] font-bold hover:bg-secondary-container/40 active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer"
              title="Start a new conversation"
            >
              <span className="material-symbols-outlined text-[16px]">add_circle</span>
              New Chat
            </button>
            <button
              onClick={async () => {
                const allMsgs = messages.filter(m => m.id !== "welcome" && m.text);
                if (allMsgs.length === 0) return;
                setSaveMsg("Saving...");
                try {
                  const h: Record<string, string> = { "Content-Type": "application/json" };
                  if (token) h["Authorization"] = `Bearer ${token}`;
                  const res = await fetch(`${API_URL}/api/v1/chat/conversations/save`, {
                    method: "POST",
                    headers: h,
                    body: JSON.stringify({
                      conversation_id: conversationId,
                      messages: allMsgs.map(m => ({ sender: m.sender, text: m.text })),
                    }),
                  });
                  if (res.ok) {
                    incrementConversationSaveCount();
                    setSaveMsg("Saved!");
                    setTimeout(() => setSaveMsg(""), 2000);
                  } else {
                    setSaveMsg("Save failed");
                    setTimeout(() => setSaveMsg(""), 3000);
                  }
                } catch (e) {
                  console.error("Save conversation failed:", e);
                  setSaveMsg("Save failed");
                  setTimeout(() => setSaveMsg(""), 3000);
                }
              }}
              className="px-3 py-1.5 rounded-xl bg-primary-container/20 text-primary text-[12px] font-bold hover:bg-primary-container/40 active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer"
              title="Save entire conversation to history"
            >
              <span className="material-symbols-outlined text-[16px]">save</span>
              Save
            </button>
          </div>
        </header>

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
                    {msg.attachments && msg.attachments.length > 0 && (
                      <AttachmentRenderer
                        attachments={msg.attachments.map((a) => ({
                          fileId: a.fileId,
                          filename: a.filename,
                          mimeType: '',
                          sizeBytes: 0,
                          type: a.type as 'pdf' | 'docx' | 'image' | 'other',
                        }))}
                      />
                    )}
                    <p className="text-body-md text-on-surface leading-relaxed">{msg.text}</p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2 max-w-[90%] flex-grow min-w-0">
                    <span className="text-label-md font-bold text-on-surface">Vyron Assistant</span>
                    <div className="glass-surface p-6 rounded-2xl rounded-tl-sm border border-outline-variant/20 shadow-xl bg-surface-container-low/60">
                      <ChatMessageRenderer content={msg.text || (isGenerating ? "..." : "")} />
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

        <footer className="p-4 sm:p-6 flex-shrink-0 border-t border-outline-variant/10 bg-surface-dim/80 backdrop-blur-md">
          <div className="max-w-4xl mx-auto">
            {/* Attached files chips */}
            {uploadedFiles.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                {uploadedFiles.map((f) => (
                  <div
                    key={f.fileId}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      background: '#1f2937',
                      border: '1px solid #374151',
                      fontSize: '12px',
                      color: '#d1d5db',
                    }}
                  >
                    <span>{f.type === 'pdf' ? '📄' : f.type === 'docx' ? '📝' : f.type === 'image' ? '🖼️' : '📎'}</span>
                    <span style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.filename}</span>
                    <button onClick={() => removeFile(f.fileId)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '0 2px' }}>✕</button>
                  </div>
                ))}
              </div>
            )}

            {/* File uploader (toggled) */}
            {showFileUploader && (
              <div style={{ marginBottom: '8px' }}>
                <FileUploader onFilesUploaded={handleFilesUploaded} />
              </div>
            )}

            <div className="glass-surface rounded-2xl border border-outline-variant/30 p-3 shadow-2xl relative">
              <div className="flex items-end gap-3 px-2">
                {/* File attach button */}
                <button
                  onClick={() => setShowFileUploader(!showFileUploader)}
                  className="w-9 h-9 flex-shrink-0 rounded-xl flex items-center justify-center hover:bg-surface-variant/50 transition-colors cursor-pointer"
                  title="Attach files"
                >
                  <span className="material-symbols-outlined text-[20px] text-on-surface-variant">attach_file</span>
                </button>

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
                  placeholder="Type your message..."
                  rows={1}
                />

                {/* Audio recorder */}
                

                {/* Send button */}
                <button
                  onClick={handleSendMessage}
                  disabled={isGenerating || (!inputQuery.trim() && uploadedFiles.length === 0)}
                  className="w-10 h-10 flex-shrink-0 bg-primary-container text-on-primary-container rounded-xl flex items-center justify-center shadow-lg shadow-primary-container/20 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <span className="material-symbols-outlined font-bold text-[20px]">arrow_upward</span>
                </button>
              </div>
            </div>
          </div>
        </footer>
      </section>
    </main>
  );
}
