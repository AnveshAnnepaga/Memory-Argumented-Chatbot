"use client";

import React, { useEffect, useRef } from "react";

export default function GraphPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const nodes = [
      { x: canvas.width / 2, y: canvas.height / 2, r: 22, label: "Core", color: "#38bdf8" },
      { x: canvas.width * 0.25, y: canvas.height * 0.35, r: 14, label: "Concept A", color: "#818cf8" },
      { x: canvas.width * 0.75, y: canvas.height * 0.35, r: 14, label: "Concept B", color: "#34d399" },
      { x: canvas.width * 0.3, y: canvas.height * 0.7, r: 12, label: "Entity 1", color: "#fb923c" },
      { x: canvas.width * 0.7, y: canvas.height * 0.7, r: 12, label: "Entity 2", color: "#a78bfa" },
      { x: canvas.width * 0.15, y: canvas.height * 0.55, r: 9, label: "Rel 1", color: "#f472b6" },
      { x: canvas.width * 0.85, y: canvas.height * 0.55, r: 9, label: "Rel 2", color: "#2dd4bf" },
    ];
    const edges = [[0,1],[0,2],[0,3],[0,4],[1,5],[2,6],[3,5],[4,6]];

    let angle = 0;
    let animId: number;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Slowly orbit satellite nodes
      nodes[1].x = canvas.width / 2 + 150 * Math.cos(angle + Math.PI * 0.7);
      nodes[1].y = canvas.height / 2 + 90 * Math.sin(angle + Math.PI * 0.7);
      nodes[2].x = canvas.width / 2 + 150 * Math.cos(angle);
      nodes[2].y = canvas.height / 2 + 90 * Math.sin(angle);
      nodes[3].x = canvas.width / 2 + 200 * Math.cos(angle + Math.PI * 1.4);
      nodes[3].y = canvas.height / 2 + 100 * Math.sin(angle + Math.PI * 1.4);
      nodes[4].x = canvas.width / 2 + 200 * Math.cos(angle + Math.PI * 0.3);
      nodes[4].y = canvas.height / 2 + 100 * Math.sin(angle + Math.PI * 0.3);
      nodes[5].x = canvas.width / 2 + 250 * Math.cos(angle + Math.PI * 1.1);
      nodes[5].y = canvas.height / 2 + 110 * Math.sin(angle + Math.PI * 1.1);
      nodes[6].x = canvas.width / 2 + 250 * Math.cos(angle - 0.2);
      nodes[6].y = canvas.height / 2 + 110 * Math.sin(angle - 0.2);

      // Draw edges
      edges.forEach(([a, b]) => {
        ctx.beginPath();
        ctx.moveTo(nodes[a].x, nodes[a].y);
        ctx.lineTo(nodes[b].x, nodes[b].y);
        ctx.strokeStyle = "rgba(56,189,248,0.18)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      // Draw nodes
      nodes.forEach((node) => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
        ctx.fillStyle = node.color + "33";
        ctx.fill();
        ctx.strokeStyle = node.color;
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = node.color;
        ctx.font = `bold ${Math.max(9, node.r * 0.55)}px Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(node.label, node.x, node.y + node.r + 10);
      });

      angle += 0.006;
      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div className="min-h-full bg-background text-on-surface pb-24 px-6 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page header */}
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center">
            <span
              className="material-symbols-outlined text-primary text-[22px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              hub
            </span>
          </div>
          <div>
            <h2 className="text-[22px] font-bold text-on-surface leading-tight">
              Knowledge Graph
            </h2>
            <p className="text-[12px] text-on-surface-variant">
              Neo4j GraphRAG · Force-Directed Entity Explorer
            </p>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Nodes", value: "—", icon: "circles_ext" },
            { label: "Relationships", value: "—", icon: "commit" },
            { label: "Entity Types", value: "—", icon: "category" },
            { label: "Subgraphs", value: "—", icon: "account_tree" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="glass-card p-4 rounded-xl border border-outline-variant/20 flex items-center gap-3"
            >
              <div className="w-9 h-9 rounded-lg bg-primary-container/20 flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-primary text-[18px]">
                  {stat.icon}
                </span>
              </div>
              <div>
                <p className="text-[12px] text-on-surface-variant">{stat.label}</p>
                <p className="text-xl font-black text-primary">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Graph canvas */}
        <div className="glass-card rounded-2xl border border-outline-variant/20 overflow-hidden" style={{ height: 360 }}>
          <div className="flex items-center justify-between px-5 py-3 border-b border-outline-variant/15">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[16px]">hub</span>
              <span className="text-[13px] font-bold text-on-surface">Graph Visualizer</span>
            </div>
            <span className="text-[11px] text-on-surface-variant font-mono">Live · Animated</span>
          </div>
          <canvas ref={canvasRef} className="w-full h-full" style={{ height: "calc(100% - 44px)" }} />
        </div>

        {/* Info card */}
        <div className="glass-card p-6 rounded-2xl border border-outline-variant/20">
          <h3 className="text-[15px] font-bold text-on-surface mb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">info</span>
            About the Knowledge Graph
          </h3>
          <p className="text-[13px] text-on-surface-variant leading-relaxed">
            Explore relationships between entities and discover connections across your knowledge base.
            Powered by Neo4j GraphRAG with force-directed entity traversal and context-aware linking.
          </p>
        </div>
      </div>
    </div>
  );
}
