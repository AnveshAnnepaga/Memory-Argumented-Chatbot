"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import Graph3DCanvas from "@/components/Graph3DCanvas";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface GraphNode {
  id: string;
  label: string;
  type: "Person" | "Organization" | "Concept";
  properties: Record<string, string | number>;
  x: number;
  y: number;
}

export default function IntelligenceGraphPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([
    {
      id: "node-1",
      label: "Julian Vance",
      type: "Person",
      properties: { role: "Principal Architect", id: "E-20491", confidence: 0.98 },
      x: 380,
      y: 300,
    },
    {
      id: "node-2",
      label: "NeuralLink Corp",
      type: "Organization",
      properties: { sector: "AI Hardware", id: "ORG-884", confidence: 0.92 },
      x: 650,
      y: 220,
    },
    {
      id: "node-3",
      label: "Quantum Memory Architecture",
      type: "Concept",
      properties: { domain: "Graph Reasoning", id: "CON-412", confidence: 0.88 },
      x: 520,
      y: 540,
    },
    {
      id: "node-4",
      label: "Antigravity Intelligence Engine",
      type: "Concept",
      properties: { domain: "Multi-Agent System", id: "SYS-001", confidence: 1.0 },
      x: 220,
      y: 420,
    },
  ]);

  const [selectedNodeId, setSelectedNodeId] = useState<string>("node-1");
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.75);
  const [stats, setStats] = useState({ total_nodes: 443, total_relationships: 1204 });

  useEffect(() => {
    axios
      .get(`${API_URL}/api/v1/graph/visualize?limit=50`)
      .then((res) => {
        if (res.data && res.data.stats) {
          setStats({
            total_nodes: res.data.stats.total_nodes || 443,
            total_relationships: res.data.stats.total_relationships || 1204,
          });
        }
      })
      .catch(() => {
        // Fallback or offline
      });
  }, []);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];

  return (
    <main className="ml-64 flex-1 relative flex flex-col min-h-screen bg-background text-on-surface overflow-hidden">
      {/* TopNavBar */}
      <header className="fixed top-0 left-64 right-0 z-50 flex justify-between items-center px-lg h-16 backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-lg">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
              search
            </span>
            <input
              className="bg-surface-container-highest border border-outline-variant/20 rounded-full pl-10 pr-6 py-1.5 text-body-sm text-on-surface w-96 focus:outline-none focus:ring-2 focus:ring-primary-container/30 placeholder:text-on-surface-variant/50"
              placeholder="Search knowledge nodes across Neo4j..."
              type="text"
            />
          </div>
        </div>
        <div className="flex items-center gap-md">
          <div className="px-3 py-1 bg-primary-container/10 border border-primary/20 rounded-full flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span className="text-label-md font-bold text-primary">Neo4j Graph Active</span>
          </div>
          <button className="p-2 hover:bg-surface-variant/30 rounded-full transition-all active:scale-95 text-on-surface-variant cursor-pointer">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="p-2 hover:bg-surface-variant/30 rounded-full transition-all active:scale-95 text-on-surface-variant cursor-pointer">
            <span className="material-symbols-outlined">contrast</span>
          </button>
        </div>
      </header>

      {/* Graph Canvas Area — fills exactly the space below the 64px header */}
      <div
        className="absolute inset-0 top-16 overflow-hidden bg-surface-dim"
        style={{ contain: "strict" }}
      >
        {/* 3D Canvas — completely centered, fills the entire available area */}
        <div className="absolute inset-0 flex items-center justify-center">
          <Graph3DCanvas
            selectedNodeId={selectedNodeId}
            onSelectNode={(n) => setSelectedNodeId(n.id)}
          />
        </div>

        {/* Left Panel: Filters & Legend */}
        <div className="absolute left-lg top-24 bottom-lg w-72 pointer-events-none flex flex-col gap-lg z-20">
          <div className="glass-card p-md rounded-xl pointer-events-auto flex flex-col gap-md border border-outline-variant/30 shadow-xl">
            <h3 className="text-label-md font-label-md text-primary tracking-widest uppercase font-bold">
              Entity Filters &amp; Stats
            </h3>
            <div className="space-y-sm">
              <div className="flex items-center justify-between group cursor-pointer p-1.5 rounded-lg hover:bg-surface-variant/30 transition-colors">
                <div className="flex items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-primary"></div>
                  <span className="text-body-sm font-semibold text-on-surface">People Nodes</span>
                </div>
                <span className="text-label-md font-label-md text-on-surface-variant">142</span>
              </div>
              <div className="flex items-center justify-between group cursor-pointer p-1.5 rounded-lg hover:bg-surface-variant/30 transition-colors">
                <div className="flex items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-secondary"></div>
                  <span className="text-body-sm font-semibold text-on-surface">Organizations</span>
                </div>
                <span className="text-label-md font-label-md text-on-surface-variant">89</span>
              </div>
              <div className="flex items-center justify-between group cursor-pointer p-1.5 rounded-lg hover:bg-surface-variant/30 transition-colors">
                <div className="flex items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-tertiary"></div>
                  <span className="text-body-sm font-semibold text-on-surface">Concepts &amp; Facts</span>
                </div>
                <span className="text-label-md font-label-md text-on-surface-variant">312</span>
              </div>
            </div>

            <div className="h-px bg-outline-variant/20"></div>

            <div className="space-y-2">
              <div className="flex justify-between text-label-md font-label-md text-on-surface-variant">
                <span>Confidence Threshold</span>
                <span className="text-primary font-bold">{Math.round(confidenceThreshold * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.99"
                step="0.01"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="w-full accent-primary h-1.5 bg-surface-container-highest rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono-code text-on-surface-variant">
                <span>0.50</span>
                <span>0.99</span>
              </div>
            </div>
          </div>

          <div className="mt-auto glass-card p-sm rounded-xl pointer-events-auto border border-outline-variant/30 shadow-xl">
            <div className="flex items-center gap-sm p-sm">
              <span className="material-symbols-outlined text-primary">insights</span>
              <p className="text-body-sm font-body-sm text-on-surface">
                Total Graph Density: <span className="font-bold text-primary">{stats.total_nodes} Nodes</span> ({stats.total_relationships} Edges)
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel: Relationship Explorer */}
        <div className="absolute right-lg top-24 bottom-lg w-80 pointer-events-none flex flex-col gap-lg z-20">
          <div className="glass-card rounded-xl pointer-events-auto flex flex-col overflow-hidden max-h-full border border-outline-variant/30 shadow-2xl">
            <div className="p-md bg-surface-container-high/50 border-b border-outline-variant/20">
              <div className="flex items-center justify-between mb-sm">
                <h3 className="text-label-md font-label-md text-primary tracking-widest uppercase font-bold">
                  Node Context
                </h3>
                <button
                  onClick={() => setSelectedNodeId("node-1")}
                  className="text-on-surface-variant hover:text-on-surface cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">refresh</span>
                </button>
              </div>
              <div className="flex items-center gap-md">
                <div className="w-12 h-12 rounded-lg bg-primary-container/10 flex items-center justify-center border border-primary-container/30">
                  <span className="material-symbols-outlined text-primary text-2xl">
                    {selectedNode.type === "Person"
                      ? "person"
                      : selectedNode.type === "Organization"
                      ? "corporate_fare"
                      : "psychology"}
                  </span>
                </div>
                <div>
                  <p className="text-body-md font-headline-md font-bold text-on-surface">{selectedNode.label}</p>
                  <p className="text-label-md font-label-md text-on-surface-variant">
                    Type: <span className="text-primary font-semibold">{selectedNode.type}</span>
                  </p>
                </div>
              </div>
            </div>

            <div className="p-md flex-1 overflow-y-auto space-y-lg custom-scrollbar">
              <section>
                <h4 className="text-label-md font-label-md text-on-surface-variant mb-sm">
                  DIRECT CONNECTIONS ({selectedNode.type === "Person" ? 2 : 1})
                </h4>
                <div className="space-y-sm">
                  <div className="p-sm bg-surface-container-low rounded-lg border border-outline-variant/10 hover:border-primary-container/50 transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-xs">
                      <span className="text-body-sm font-bold text-on-surface">
                        {selectedNode.type === "Person" ? "NeuralLink Corp" : "Julian Vance"}
                      </span>
                      <span className="text-[10px] bg-secondary-container/20 text-secondary px-1 py-0.5 rounded font-bold">
                        {selectedNode.type === "Person" ? "Org" : "Person"}
                      </span>
                    </div>
                    <p className="text-label-md font-label-md text-on-surface-variant mb-sm">
                      Relation: {selectedNode.type === "Person" ? "EMPLOYED_BY" : "LEADS_PROJECT"}
                    </p>
                    <div className="flex items-center gap-sm">
                      <div className="flex-1 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                        <div className="h-full bg-secondary w-[92%]"></div>
                      </div>
                      <span className="text-[10px] font-mono-code text-secondary">0.92</span>
                    </div>
                  </div>

                  <div className="p-sm bg-surface-container-low rounded-lg border border-outline-variant/10 hover:border-primary-container/50 transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-xs">
                      <span className="text-body-sm font-bold text-on-surface">Quantum Memory Architecture</span>
                      <span className="text-[10px] bg-tertiary-container/20 text-tertiary px-1 py-0.5 rounded font-bold">
                        Concept
                      </span>
                    </div>
                    <p className="text-label-md font-label-md text-on-surface-variant mb-sm">Relation: RESEARCHES</p>
                    <div className="flex items-center gap-sm">
                      <div className="flex-1 h-1 bg-surface-container-highest rounded-full overflow-hidden">
                        <div className="h-full bg-tertiary w-[88%]"></div>
                      </div>
                      <span className="text-[10px] font-mono-code text-tertiary">0.88</span>
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h4 className="text-label-md font-label-md text-on-surface-variant mb-sm">AI INFERENCE &amp; CORRELATION</h4>
                <div className="p-md rounded-lg border-l-2 border-primary bg-primary-container/5">
                  <p className="text-body-sm font-body-sm text-primary italic leading-relaxed">
                    &ldquo;Strong correlation between {selectedNode.label}&apos;s recent vector chunks and the multi-hop Neo4j entity graph (94% confidence). Suggests structural convergence with LangGraph routing policies.&rdquo;
                  </p>
                </div>
              </section>
            </div>

            <div className="p-md bg-surface-container-high/30 border-t border-outline-variant/20">
              <button
                onClick={() => alert(`Deep tracing Neo4j relationships for ${selectedNode.label}...`)}
                className="w-full py-2 bg-primary-container text-on-primary-container font-bold rounded-lg hover:opacity-90 active:scale-95 transition-all text-label-md uppercase tracking-wider cursor-pointer shadow-md"
              >
                Deep Trace Entity
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Left: Minimap */}
        <div className="absolute left-lg bottom-lg w-48 h-28 glass-card rounded-lg border border-outline-variant/40 overflow-hidden pointer-events-auto z-20 shadow-xl hidden sm:block">
          <div className="relative w-full h-full opacity-60 p-sm">
            <div className="absolute w-2.5 h-2.5 bg-primary rounded-full top-1/4 left-1/3 animate-pulse"></div>
            <div className="absolute w-2 h-2 bg-secondary rounded-full top-1/2 left-1/2"></div>
            <div className="absolute w-2 h-2 bg-tertiary rounded-full top-3/4 left-1/4"></div>
            <div className="absolute w-2.5 h-2.5 bg-primary rounded-full top-1/3 right-1/4"></div>
            <div className="absolute top-3 left-4 w-14 h-12 border border-primary bg-primary/10 rounded"></div>
          </div>
        </div>

        {/* Canvas Controls */}
        <div className="absolute bottom-lg right-[340px] glass-card flex rounded-lg p-1.5 gap-1 pointer-events-auto border border-outline-variant/40 z-20 shadow-xl">
          <button className="p-2 hover:bg-surface-variant/50 rounded transition-colors text-on-surface-variant cursor-pointer">
            <span className="material-symbols-outlined text-[20px]">add</span>
          </button>
          <div className="w-px bg-outline-variant/20 my-1"></div>
          <button className="p-2 hover:bg-surface-variant/50 rounded transition-colors text-on-surface-variant cursor-pointer">
            <span className="material-symbols-outlined text-[20px]">remove</span>
          </button>
          <div className="w-px bg-outline-variant/20 my-1"></div>
          <button className="p-2 hover:bg-surface-variant/50 rounded transition-colors text-on-surface-variant cursor-pointer">
            <span className="material-symbols-outlined text-[20px]">fit_screen</span>
          </button>
        </div>
      </div>
    </main>
  );
}
