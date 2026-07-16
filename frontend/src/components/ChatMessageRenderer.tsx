"use client";

import React, { useState } from "react";

interface ChatMessageRendererProps {
  content: string;
}

export default function ChatMessageRenderer({ content }: ChatMessageRendererProps) {
  const [copiedCodeIndex, setCopiedCodeIndex] = useState<number | null>(null);

  // 1. Strip any accidental JSON wrapper (safety net)
  let cleanContent = content || "";
  const trimmed = cleanContent.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    try {
      const parsed = JSON.parse(trimmed);
      if (typeof parsed === "object" && parsed !== null) {
        const extracted =
          parsed.response ||
          parsed.answer ||
          parsed.content ||
          parsed.text ||
          parsed.output ||
          (parsed.data && (parsed.data.response || parsed.data.answer || parsed.data.content));
        if (extracted && typeof extracted === "string" && extracted.trim()) {
          cleanContent = extracted.trim();
        }
      }
    } catch {
      // Not valid JSON, keep as-is
    }
  }

  // 2. Extract fenced code blocks (``` ... ```)
  const codeBlockRegex = /```([\w-]*)\n([\s\S]*?)```/g;
  const parts: { type: "text" | "code"; lang?: string; text: string }[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(cleanContent)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", text: cleanContent.slice(lastIndex, match.index) });
    }
    parts.push({ type: "code", lang: match[1] || "code", text: match[2].trim() });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < cleanContent.length) {
    parts.push({ type: "text", text: cleanContent.slice(lastIndex) });
  }

  const handleCopyCode = (codeText: string, idx: number) => {
    navigator.clipboard.writeText(codeText);
    setCopiedCodeIndex(idx);
    setTimeout(() => setCopiedCodeIndex(null), 2000);
  };

  // 3. Inline formatters: bold (**text**) and inline code (`code`)
  const formatBold = (str: string): React.ReactNode[] => {
    const boldRegex = /\*\*([^*]+)\*\*/g;
    const items: React.ReactNode[] = [];
    let lIdx = 0;
    let bm: RegExpExecArray | null;
    while ((bm = boldRegex.exec(str)) !== null) {
      if (bm.index > lIdx) items.push(str.slice(lIdx, bm.index));
      items.push(<strong key={`b-${bm.index}`} className="font-semibold text-on-surface">{bm[1]}</strong>);
      lIdx = bm.index + bm[0].length;
    }
    if (lIdx < str.length) items.push(str.slice(lIdx));
    return items;
  };

  const formatInline = (text: string): React.ReactNode[] => {
    const inlineCode = /`([^`]+)`/g;
    const segments: React.ReactNode[] = [];
    let lastIdx = 0;
    let m: RegExpExecArray | null;
    while ((m = inlineCode.exec(text)) !== null) {
      if (m.index > lastIdx) segments.push(...formatBold(text.slice(lastIdx, m.index)));
      segments.push(
        <code key={`ic-${m.index}`} className="bg-primary/15 text-primary font-mono px-1.5 py-0.5 rounded text-[12px] border border-primary/20">
          {m[1]}
        </code>
      );
      lastIdx = m.index + m[0].length;
    }
    if (lastIdx < text.length) segments.push(...formatBold(text.slice(lastIdx)));
    return segments;
  };

  // 4. Line-level Markdown rendering (headings, bullets, numbered lists)
  const renderLines = (raw: string, chunkIdx: number) => {
    return raw.split("\n").map((line, li) => {
      const key = `${chunkIdx}-${li}`;
      const t = line.trim();

      if (t.startsWith("### ")) return (
        <h3 key={key} className="text-[13px] font-bold text-secondary mt-3 mb-1 uppercase tracking-wider">
          {formatInline(t.slice(4))}
        </h3>
      );
      if (t.startsWith("## ")) return (
        <h2 key={key} className="text-[15px] font-bold text-on-surface mt-4 mb-1.5 pb-1 border-b border-outline-variant/20">
          {formatInline(t.slice(3))}
        </h2>
      );
      if (t.startsWith("# ")) return (
        <h1 key={key} className="text-[17px] font-bold text-primary mt-4 mb-2 tracking-tight">
          {formatInline(t.slice(2))}
        </h1>
      );

      // Horizontal rule
      if (t === "---" || t === "***") return <hr key={key} className="border-outline-variant/20 my-3" />;

      // Bullet list items
      if (t.startsWith("- ") || t.startsWith("* ")) return (
        <div key={key} className="flex items-start gap-2.5 my-0.5 pl-1">
          <span className="w-1.5 h-1.5 rounded-full bg-primary/70 mt-[9px] flex-shrink-0" />
          <p className="text-[14px] text-on-surface leading-relaxed flex-1">{formatInline(t.slice(2))}</p>
        </div>
      );

      // Numbered list items
      const nm = t.match(/^(\d+)\.\s+(.*)/);
      if (nm) return (
        <div key={key} className="flex items-start gap-2.5 my-0.5 pl-1">
          <span className="font-bold text-primary text-[13px] font-mono mt-0.5 flex-shrink-0 w-5">{nm[1]}.</span>
          <p className="text-[14px] text-on-surface leading-relaxed flex-1">{formatInline(nm[2])}</p>
        </div>
      );

      // Blank line → small spacer
      if (!t) return <div key={key} className="h-1.5" />;

      // Normal paragraph
      return (
        <p key={key} className="text-[14px] text-on-surface leading-relaxed my-0.5">
          {formatInline(line)}
        </p>
      );
    });
  };

  // 5. Render
  return (
    <div className="space-y-0.5 break-words w-full">
      {parts.map((part, idx) => {
        if (part.type === "code") {
          const copied = copiedCodeIndex === idx;
          return (
            <div key={idx} className="my-3 rounded-xl border border-outline-variant/30 bg-[#0d1117] overflow-hidden shadow-lg">
              {/* Code header */}
              <div className="flex items-center justify-between px-4 py-2 bg-surface-container border-b border-outline-variant/20">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-red-500/60" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500/60" />
                    <span className="w-3 h-3 rounded-full bg-green-500/60" />
                  </div>
                  <span className="text-[11px] font-mono font-bold tracking-widest text-primary uppercase ml-1">
                    {part.lang || "code"}
                  </span>
                </div>
                <button
                  onClick={() => handleCopyCode(part.text, idx)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg hover:bg-surface-variant/40 text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer text-[11px]"
                >
                  <span className="material-symbols-outlined text-[14px]">
                    {copied ? "check" : "content_copy"}
                  </span>
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              {/* Code body */}
              <pre className="p-4 overflow-x-auto font-mono text-[13px] leading-relaxed text-[#c9d1d9]">
                <code>{part.text}</code>
              </pre>
            </div>
          );
        }
        return <div key={idx}>{renderLines(part.text, idx)}</div>;
      })}
    </div>
  );
}
