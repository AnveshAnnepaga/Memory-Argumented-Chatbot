"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  size_bytes?: number;
  status: string;
  created_at?: string;
  chunks_count?: number;
}

export default function KnowledgeCenterPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([
    {
      id: "doc-1",
      filename: "2026_Enterprise_Security_Manifesto.pdf",
      file_type: "PDF",
      size_bytes: 12400000,
      status: "INDEXED",
      created_at: "2026-07-15",
      chunks_count: 84,
    },
    {
      id: "doc-2",
      filename: "docs.antigravity.ai/architecture/v15",
      file_type: "URL",
      size_bytes: 0,
      status: "INDEXED",
      created_at: "2026-07-14",
      chunks_count: 42,
    },
    {
      id: "doc-3",
      filename: "LangGraph_Hybrid_Routing_Policy.docx",
      file_type: "DOCX",
      size_bytes: 450000,
      status: "INDEXED",
      created_at: "2026-07-12",
      chunks_count: 18,
    },
  ]);
  const [activeFilter, setActiveFilter] = useState("All");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    axios
      .get(`${API_URL}/api/v1/knowledge/documents`)
      .then((res) => {
        if (res.data && Array.isArray(res.data.documents) && res.data.documents.length > 0) {
          setDocuments(res.data.documents);
        }
      })
      .catch(() => {
        // Fallback to initial high-fidelity sample state if backend is offline
      });
  }, []);

  const handleSimulateUpload = () => {
    setIsUploading(true);
    setUploadProgress(15);
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          setDocuments((old) => [
            {
              id: `doc-${Date.now()}`,
              filename: "Production_Vector_Embeddings_Log.pdf",
              file_type: "PDF",
              size_bytes: 8400000,
              status: "INDEXED",
              created_at: new Date().toISOString().split("T")[0],
              chunks_count: 112,
            },
            ...old,
          ]);
          return 0;
        }
        return prev + 25;
      });
    }, 600);
  };

  const filteredDocs = documents.filter((doc) => {
    if (activeFilter === "Documents") return doc.file_type === "PDF" || doc.file_type === "DOCX";
    if (activeFilter === "URLs") return doc.file_type === "URL";
    return true;
  });

  return (
    <main className="ml-64 pt-16 min-h-screen bg-background text-on-surface pb-24">
      {/* Top Header Bar */}
      <header className="h-16 border-b border-outline-variant/20 bg-surface-container/50 backdrop-blur-md flex items-center justify-between px-lg fixed top-0 right-0 left-64 z-30">
        <div className="flex items-center gap-md">
          <span className="text-headline-md font-headline-md font-bold text-on-surface">Knowledge Center</span>
          <span className="text-label-md px-2.5 py-0.5 bg-primary-container/10 text-primary border border-primary/20 rounded-full font-bold">
            Pinecone &amp; Neo4j Synced
          </span>
        </div>
        <div className="flex items-center gap-sm">
          <span className="text-label-md text-on-surface-variant">Hybrid Sparse-Dense RAG Active</span>
        </div>
      </header>

      <div className="p-lg md:p-margin-desktop max-w-[1600px] mx-auto space-y-lg">
        {/* Page Header & Stats */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-lg">
          <div className="space-y-sm">
            <div className="flex items-center gap-2 text-primary font-mono-code text-label-md uppercase tracking-[0.2em]">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              Neural Knowledge Base
            </div>
            <h1 className="text-headline-lg font-headline-lg text-on-surface">Vector &amp; Graph Indexing</h1>
          </div>
          <div className="flex flex-wrap gap-md">
            <div className="glass-surface px-lg py-md rounded-xl flex items-center gap-md border border-outline-variant/10">
              <div className="p-3 rounded-lg bg-surface-container-high text-primary">
                <span className="material-symbols-outlined">database</span>
              </div>
              <div>
                <p className="text-label-md font-label-md text-on-surface-variant">Total Sources</p>
                <p className="text-headline-md font-headline-md font-bold">{documents.length + 1200}</p>
              </div>
            </div>
            <div className="glass-surface px-lg py-md rounded-xl flex items-center gap-md border border-outline-variant/10">
              <div className="p-3 rounded-lg bg-surface-container-high text-tertiary">
                <span className="material-symbols-outlined">article</span>
              </div>
              <div>
                <p className="text-label-md font-label-md text-on-surface-variant">Indexed Chunks</p>
                <p className="text-headline-md font-headline-md font-bold">48,291</p>
              </div>
            </div>
            <div className="glass-surface px-lg py-md rounded-xl flex items-center gap-md border border-outline-variant/10">
              <div className="p-3 rounded-lg bg-surface-container-high text-secondary">
                <span className="material-symbols-outlined">sync</span>
              </div>
              <div>
                <p className="text-label-md font-label-md text-on-surface-variant">Processing Queue</p>
                <p className="text-headline-md font-headline-md font-bold">{isUploading ? "1" : "0"}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Layout Grid */}
        <div className="grid grid-cols-12 gap-lg">
          {/* Left Column: Knowledge Management */}
          <div className="col-span-12 xl:col-span-9 space-y-lg">
            {/* Upload Zone */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
              <div
                onClick={handleSimulateUpload}
                className="glass-surface border-2 border-dashed border-outline-variant/30 rounded-xl p-lg flex flex-col items-center justify-center text-center group hover:border-primary/50 transition-all cursor-pointer relative overflow-hidden h-64 shadow-lg shadow-black/20"
              >
                <div className="mb-4 p-4 rounded-full bg-surface-container-highest text-primary-container group-hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined text-[40px]">upload_file</span>
                </div>
                <h3 className="text-body-lg font-bold mb-1 text-on-surface">Ingest New Intelligence</h3>
                <p className="text-body-sm text-on-surface-variant">Click or Drag &amp; Drop PDF, DOCX, or Paste URL</p>
                <div className="mt-4 flex gap-2">
                  <span className="text-label-md font-label-md bg-surface-variant/40 px-3 py-1 rounded-full border border-outline-variant/20">.pdf</span>
                  <span className="text-label-md font-label-md bg-surface-variant/40 px-3 py-1 rounded-full border border-outline-variant/20">.docx</span>
                  <span className="text-label-md font-label-md bg-surface-variant/40 px-3 py-1 rounded-full border border-outline-variant/20">.txt</span>
                </div>
              </div>

              {/* Processing Mockup or Active Status */}
              <div className="glass-surface rounded-xl p-lg flex flex-col justify-between border border-outline-variant/10 h-64 relative overflow-hidden shadow-lg shadow-black/20">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-sm">
                    <span className="material-symbols-outlined text-primary text-[28px]">description</span>
                    <div>
                      <h4 className="text-body-md font-bold text-on-surface">
                        {isUploading ? "Production_Vector_Embeddings_Log.pdf" : "System_Architecture_Knowledge.pdf"}
                      </h4>
                      <p className="text-label-md text-on-surface-variant">
                        {isUploading ? "8.4 MB • Processing Vector Embeddings" : "12.4 MB • Fully Indexed & Grounded"}
                      </p>
                    </div>
                  </div>
                  <span className="text-label-md font-label-md text-primary animate-pulse">
                    {isUploading ? `${uploadProgress}%` : "100%"}
                  </span>
                </div>

                <div className="space-y-md">
                  <div className="flex justify-between text-label-md font-label-md text-on-surface-variant">
                    <span className={uploadProgress >= 25 ? "text-primary" : ""}>Tokenization</span>
                    <span className={uploadProgress >= 50 ? "text-primary" : ""}>Chunking</span>
                    <span className={uploadProgress >= 75 ? "text-primary" : ""}>Pinecone Embedding</span>
                  </div>
                  <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-primary h-full rounded-full transition-all duration-300 relative"
                      style={{ width: `${isUploading ? uploadProgress : 100}%` }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[shimmer_2s_infinite]"></div>
                    </div>
                  </div>
                  <p className="text-body-sm italic text-on-surface-variant/80">
                    {isUploading
                      ? '"Extracting hierarchical semantic chunks & cross-encoder vectors..."'
                      : '"Ready for sub-180ms hybrid semantic retrieval across all shards."'}
                  </p>
                </div>

                <div className="flex justify-end gap-sm">
                  <button
                    onClick={() => setIsUploading(false)}
                    className="text-label-md font-label-md px-4 py-2 rounded-lg border border-outline-variant/30 hover:bg-surface-variant/40 transition-all cursor-pointer"
                  >
                    {isUploading ? "Cancel" : "Refresh Index"}
                  </button>
                  <button className="text-label-md font-label-md px-4 py-2 rounded-lg bg-primary-container text-on-primary-container font-bold shadow-md cursor-pointer">
                    View Vector Shards
                  </button>
                </div>
              </div>
            </div>

            {/* Filter & Search Toolbar */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-md glass-surface p-sm rounded-xl border border-outline-variant/10">
              <div className="flex items-center gap-1 p-1 bg-surface-container-lowest rounded-lg">
                {["All", "Documents", "URLs", "Datasets"].map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setActiveFilter(filter)}
                    className={`px-6 py-2 rounded-md text-label-md font-bold transition-all cursor-pointer ${
                      activeFilter === filter
                        ? "bg-primary-container text-on-primary-container shadow-sm"
                        : "hover:bg-surface-variant/40 text-on-surface-variant"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-sm pr-sm">
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
                  <span className="material-symbols-outlined">filter_list</span>
                </button>
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
                  <span className="material-symbols-outlined">sort</span>
                </button>
              </div>
            </div>

            {/* Document Table */}
            <div className="glass-surface rounded-xl overflow-hidden border border-outline-variant/10 shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-surface-container-high/50 border-b border-outline-variant/10">
                    <tr>
                      <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                        Document Name
                      </th>
                      <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                        Size / Chunks
                      </th>
                      <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                        Date Indexed
                      </th>
                      <th className="px-lg py-4 text-label-md font-label-md text-on-surface-variant uppercase tracking-wider text-right">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/10">
                    {filteredDocs.map((doc) => (
                      <tr key={doc.id} className="hover:bg-surface-variant/20 transition-colors group">
                        <td className="px-lg py-4">
                          <div className="flex items-center gap-md">
                            <div
                              className={`p-2 rounded bg-surface-container ${
                                doc.file_type === "PDF"
                                  ? "text-primary"
                                  : doc.file_type === "URL"
                                  ? "text-secondary"
                                  : "text-tertiary"
                              }`}
                            >
                              <span className="material-symbols-outlined text-[20px]">
                                {doc.file_type === "PDF"
                                  ? "picture_as_pdf"
                                  : doc.file_type === "URL"
                                  ? "link"
                                  : "description"}
                              </span>
                            </div>
                            <span className="text-body-sm font-bold text-on-surface">{doc.filename}</span>
                          </div>
                        </td>
                        <td className="px-lg py-4 text-body-sm text-on-surface-variant">{doc.file_type}</td>
                        <td className="px-lg py-4 text-body-sm text-on-surface-variant">
                          {doc.size_bytes
                            ? `${(doc.size_bytes / 1024 / 1024).toFixed(1)} MB (${doc.chunks_count || 40} chunks)`
                            : `${doc.chunks_count || 42} chunks`}
                        </td>
                        <td className="px-lg py-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-tertiary/10 text-tertiary-container border border-tertiary/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-tertiary-container"></span>
                            {doc.status || "INDEXED"}
                          </span>
                        </td>
                        <td className="px-lg py-4 text-body-sm text-on-surface-variant">
                          {doc.created_at || "Oct 12, 2026"}
                        </td>
                        <td className="px-lg py-4 text-right">
                          <div className="flex justify-end gap-sm opacity-60 group-hover:opacity-100 transition-opacity">
                            <button className="p-1.5 hover:text-primary transition-colors cursor-pointer">
                              <span className="material-symbols-outlined text-[20px]">visibility</span>
                            </button>
                            <button className="p-1.5 hover:text-error transition-colors cursor-pointer">
                              <span className="material-symbols-outlined text-[20px]">delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-lg border-t border-outline-variant/10 flex justify-between items-center bg-surface-container-low/30">
                <p className="text-label-md text-on-surface-variant">
                  Showing 1-{filteredDocs.length} of {documents.length + 1200} documents
                </p>
                <div className="flex items-center gap-sm">
                  <button className="p-2 rounded-lg bg-surface-container-high hover:bg-surface-variant/60 transition-colors cursor-pointer">
                    <span className="material-symbols-outlined text-[18px]">chevron_left</span>
                  </button>
                  <span className="text-label-md px-3 font-bold text-on-surface">1 / 121</span>
                  <button className="p-2 rounded-lg bg-surface-container-high hover:bg-surface-variant/60 transition-colors cursor-pointer">
                    <span className="material-symbols-outlined text-[18px]">chevron_right</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Activity Sidebar */}
          <div className="col-span-12 xl:col-span-3 space-y-lg">
            <div className="space-y-md">
              <h2 className="text-body-md font-bold flex items-center gap-2 text-on-surface">
                <span className="material-symbols-outlined text-secondary">bolt</span>
                Latest Activity
              </h2>

              {/* Activity Feed Glass Cards */}
              <div className="space-y-sm">
                <div className="glass-surface p-md rounded-xl ai-reasoning-line border border-outline-variant/10 hover:translate-x-1 transition-transform cursor-pointer">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-label-md font-bold text-secondary">Index Updated</span>
                    <span className="text-[10px] text-on-surface-variant">2m ago</span>
                  </div>
                  <p className="text-body-sm font-medium mb-1 text-on-surface">Vector cluster #829 optimized.</p>
                  <p className="text-[11px] text-on-surface-variant/70 italic">
                    Retrieved 42 new cross-references from Security Manifesto.
                  </p>
                </div>

                <div className="glass-surface p-md rounded-xl border border-outline-variant/10 hover:translate-x-1 transition-transform cursor-pointer opacity-80">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-label-md font-bold text-tertiary">New Source Ingested</span>
                    <span className="text-[10px] text-on-surface-variant">1h ago</span>
                  </div>
                  <p className="text-body-sm font-medium mb-1 text-on-surface">LangGraph_Hybrid_Routing_Policy.docx</p>
                  <p className="text-[11px] text-on-surface-variant/70">Source: External DOCX • User: Anvesh Mishra</p>
                </div>

                <div className="glass-surface p-md rounded-xl border border-outline-variant/10 hover:translate-x-1 transition-transform cursor-pointer opacity-60">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-label-md font-bold text-primary">System Notice</span>
                    <span className="text-[10px] text-on-surface-variant">Yesterday</span>
                  </div>
                  <p className="text-body-sm font-medium mb-1 text-on-surface">Pinecone BM25 Sparse Index Synced</p>
                  <p className="text-[11px] text-on-surface-variant/70">Latency improved by 14.2ms across all queries.</p>
                </div>
              </div>
            </div>

            {/* Storage & Index Health */}
            <div className="glass-surface p-lg rounded-xl border border-outline-variant/10 space-y-md">
              <h3 className="text-label-md font-bold text-on-surface uppercase tracking-wider">Vector Shard Health</h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-[12px] mb-1">
                    <span className="text-on-surface-variant">Pinecone Dense Storage</span>
                    <span className="font-bold text-primary">64% (3.2 GB)</span>
                  </div>
                  <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div className="bg-primary h-full w-[64%] shadow-[0_0_8px_#00e5ff]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[12px] mb-1">
                    <span className="text-on-surface-variant">Neo4j Graph Relationships</span>
                    <span className="font-bold text-secondary">41% (1.8M Edges)</span>
                  </div>
                  <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div className="bg-secondary h-full w-[41%] shadow-[0_0_8px_#d2bbff]"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
