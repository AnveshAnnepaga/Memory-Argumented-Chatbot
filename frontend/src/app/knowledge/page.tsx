"use client";

import React, { useState, useCallback } from "react";
import FileUploader from "@/components/FileUploader";
import { api } from "@/lib/api";

interface UploadedFileInfo {
  fileId: string;
  filename: string;
  type: 'pdf' | 'docx' | 'image' | 'other';
  uploading: boolean;
  error?: string;
}

interface DocumentItem {
  id: string;
  title: string;
  source: string;
  category: string;
  word_count: number;
  updated_at: string;
  chunks: number;
}

export default function KnowledgeCenterPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [showUploader, setShowUploader] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<DocumentItem[]>([]);

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.get<{ documents: DocumentItem[] }>('/knowledge/documents', { skip: 0, limit: 50 });
      if (data && Array.isArray(data.documents)) {
        setDocuments(data.documents);
      }
    } catch {
      // silently fail
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleFilesUploaded = useCallback((files: UploadedFileInfo[]) => {
    setUploadedFiles((prev) => [...prev, ...files]);
    setShowUploader(false);
    setTimeout(() => loadDocuments(), 1000);
  }, [loadDocuments]);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setIsLoading(true);
    try {
      const data = await api.get<{ results: DocumentItem[] }>('/knowledge/query', { q: searchQuery, top_k: 10 });
      if (data && Array.isArray(data.results)) {
        setSearchResults(data.results);
      }
    } catch {
      // silently fail
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery]);

  const displayDocs = searchResults.length > 0 ? searchResults : documents;

  return (
    <div className="min-h-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center">
              <span
                className="material-symbols-outlined text-primary text-[22px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                auto_stories
              </span>
            </div>
            <div>
              <h2 className="text-[22px] font-bold text-on-surface leading-tight">
                Knowledge Base
              </h2>
              <p className="text-[12px] text-on-surface-variant">
                Upload PDFs, DOCX, images, or audio to build your knowledge base
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowUploader(!showUploader)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-container text-on-primary-container text-[13px] font-bold rounded-xl hover:brightness-110 active:scale-95 transition-all shadow-md shadow-primary-container/20"
          >
            <span className="material-symbols-outlined text-[16px]">upload_file</span>
            Upload
          </button>
        </div>

        {/* Upload area (toggled) */}
        {showUploader && (
          <div className="glass-card p-4 rounded-xl border border-outline-variant/20">
            <FileUploader onFilesUploaded={handleFilesUploaded} />
            {uploadedFiles.length > 0 && (
              <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {uploadedFiles.filter(f => !f.uploading).map((f) => (
                  <div key={f.fileId} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: f.error ? '#ef4444' : '#10b981' }}>
                    <span>{f.error ? '✗' : '✓'}</span>
                    <span>{f.filename}</span>
                    {f.error && <span style={{ color: '#ef4444' }}>{f.error}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Documents", value: documents.length.toString() || "—", icon: "description" },
            { label: "Uploaded Files", value: uploadedFiles.length.toString() || "0", icon: "upload_file" },
            { label: "Vector Dims", value: "1024", icon: "scatter_plot" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="glass-card p-5 rounded-xl border border-outline-variant/20 flex items-center gap-4"
            >
              <div className="w-10 h-10 rounded-lg bg-primary-container/20 flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-primary text-[20px]">
                  {stat.icon}
                </span>
              </div>
              <div>
                <p className="text-[13px] text-on-surface-variant">{stat.label}</p>
                <p className="text-2xl font-black text-primary">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Search bar */}
        <div className="glass-surface rounded-xl border border-outline-variant/20 flex items-center gap-3 px-4 py-3 shadow-lg">
          <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
            placeholder="Search the knowledge base..."
            className="flex-1 bg-transparent border-none focus:outline-none text-[14px] text-on-surface placeholder:text-on-surface-variant/40"
          />
          {searchQuery && (
            <button
              onClick={() => { setSearchQuery(""); setSearchResults([]); }}
              className="text-on-surface-variant hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          )}
        </div>

        {/* Documents list */}
        <div className="glass-card p-8 rounded-2xl border border-outline-variant/20">
          <h3 className="text-[16px] font-bold text-on-surface mb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">library_books</span>
            Indexed Documents
          </h3>
          <p className="text-[13px] text-on-surface-variant mb-6">
            Search and explore indexed knowledge to power informed answers across all conversations.
          </p>

          {isLoading && (
            <div className="flex justify-center py-8">
              <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
            </div>
          )}

          {!isLoading && displayDocs.length === 0 && uploadedFiles.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <span
                className="material-symbols-outlined text-on-surface-variant/30 text-6xl"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                auto_stories
              </span>
              <div className="text-center">
                <p className="text-[15px] font-semibold text-on-surface-variant">No documents indexed yet</p>
                <p className="text-[13px] text-on-surface-variant/60 mt-1">
                  Upload documents to populate your knowledge base.
                </p>
              </div>
              <button
                onClick={() => setShowUploader(true)}
                className="mt-2 flex items-center gap-2 px-5 py-2.5 bg-primary-container text-on-primary-container text-[13px] font-bold rounded-xl hover:brightness-110 active:scale-95 transition-all"
              >
                <span className="material-symbols-outlined text-[16px]">upload_file</span>
                Upload First Document
              </button>
            </div>
          )}

          {!isLoading && displayDocs.length > 0 && (
            <div className="space-y-3">
              {displayDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-surface-variant/20 border border-outline-variant/10 hover:border-primary/30 transition-all"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="material-symbols-outlined text-primary text-[20px]">description</span>
                    <div className="min-w-0">
                      <p className="text-[14px] font-semibold text-on-surface truncate">{doc.title}</p>
                      <p className="text-[11px] text-on-surface-variant">
                        {doc.source} · {doc.word_count?.toLocaleString()} words · {doc.chunks || 0} chunks
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] text-on-surface-variant flex-shrink-0">{doc.category}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
