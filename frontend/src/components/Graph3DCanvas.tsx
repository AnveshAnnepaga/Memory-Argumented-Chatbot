"use client";

import React, { useEffect, useRef, useState } from "react";

export interface Node3D {
  id: string;
  label: string;
  type: "Person" | "Organization" | "Concept" | "Memory";
  confidence: number;
  x: number;
  y: number;
  z: number;
  vx?: number;
  vy?: number;
  vz?: number;
  color?: string;
}

export interface Link3D {
  source: string;
  target: string;
  relation: string;
}

interface Graph3DCanvasProps {
  initialNodes?: Node3D[];
  initialLinks?: Link3D[];
  onSelectNode?: (node: Node3D) => void;
  selectedNodeId?: string | null;
}

const DEFAULT_NODES: Node3D[] = [
  { id: "1", label: "Anvesh Mishra", type: "Person", confidence: 0.99, x: 0, y: 0, z: 0, color: "#00E5FF" },
  { id: "2", label: "Antigravity Studio", type: "Organization", confidence: 0.98, x: 180, y: -120, z: 140, color: "#D2BBFF" },
  { id: "3", label: "LangGraph Orchestration", type: "Concept", confidence: 0.96, x: -200, y: 150, z: -100, color: "#6FFBBE" },
  { id: "4", label: "Hybrid RAG Pipeline", type: "Concept", confidence: 0.95, x: 220, y: 160, z: -160, color: "#6FFBBE" },
  { id: "5", label: "Neo4j Knowledge Graph", type: "Concept", confidence: 0.97, x: -180, y: -160, z: 180, color: "#6FFBBE" },
  { id: "6", label: "Long-Term Memory", type: "Memory", confidence: 0.99, x: 60, y: 220, z: 120, color: "#FF9800" },
  { id: "7", label: "Groq Llama-3 Engine", type: "Concept", confidence: 0.98, x: -80, y: -240, z: -150, color: "#00E5FF" },
  { id: "8", label: "Tool Execution Layer", type: "Concept", confidence: 0.92, x: 260, y: -60, z: -80, color: "#D2BBFF" },
];

const DEFAULT_LINKS: Link3D[] = [
  { source: "1", target: "2", relation: "FOUNDED" },
  { source: "1", target: "6", relation: "STORES_PROFILE" },
  { source: "2", target: "3", relation: "ORCHESTRATES" },
  { source: "3", target: "4", relation: "QUERIES_VECTORS" },
  { source: "3", target: "5", relation: "TRAVERSES_GRAPH" },
  { source: "3", target: "7", relation: "GENERATES_LLM" },
  { source: "3", target: "8", relation: "CALLS_TOOLS" },
  { source: "4", target: "5", relation: "HYBRID_MERGE" },
  { source: "6", target: "3", relation: "INJECTS_FACTS" },
];

export default function Graph3DCanvas({
  initialNodes = DEFAULT_NODES,
  initialLinks = DEFAULT_LINKS,
  onSelectNode,
  selectedNodeId,
}: Graph3DCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isHovering, setIsHovering] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<Node3D | null>(null);

  // Rotation angles in 3D space
  const rotRef = useRef({ yaw: 0.4, pitch: 0.3, autoRotate: true });
  const dragRef = useRef({ isDragging: false, startX: 0, startY: 0, lastYaw: 0, lastPitch: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    const fov = 550; // Camera field of view depth

    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Auto-rotate gently if not dragging
      if (rotRef.current.autoRotate && !dragRef.current.isDragging) {
        rotRef.current.yaw += 0.003;
      }

      const cosY = Math.cos(rotRef.current.yaw);
      const sinY = Math.sin(rotRef.current.yaw);
      const cosP = Math.cos(rotRef.current.pitch);
      const sinP = Math.sin(rotRef.current.pitch);

      // Project 3D nodes to 2D screen coordinates with depth sorting
      const projectedNodes = initialNodes.map((n) => {
        // Rotate Y (yaw)
        const x1 = n.x * cosY - n.z * sinY;
        const z1 = n.z * cosY + n.x * sinY;
        // Rotate X (pitch)
        const y2 = n.y * cosP - z1 * sinP;
        const z2 = z1 * cosP + n.y * sinP;

        const scale = fov / (fov + z2 + 400);
        const screenX = centerX + x1 * scale;
        const screenY = centerY + y2 * scale;

        return {
          ...n,
          screenX,
          screenY,
          scale,
          zDepth: z2,
        };
      });

      // Sort nodes back-to-front so closer nodes draw on top
      projectedNodes.sort((a, b) => b.zDepth - a.zDepth);

      // Draw 3D Connection Links
      initialLinks.forEach((link) => {
        const sourceNode = projectedNodes.find((n) => n.id === link.source);
        const targetNode = projectedNodes.find((n) => n.id === link.target);
        if (!sourceNode || !targetNode) return;

        ctx.beginPath();
        ctx.moveTo(sourceNode.screenX, sourceNode.screenY);
        ctx.lineTo(targetNode.screenX, targetNode.screenY);

        const isLinkActive =
          selectedNodeId === sourceNode.id ||
          selectedNodeId === targetNode.id ||
          hoveredNode?.id === sourceNode.id ||
          hoveredNode?.id === targetNode.id;

        const gradient = ctx.createLinearGradient(
          sourceNode.screenX,
          sourceNode.screenY,
          targetNode.screenX,
          targetNode.screenY
        );
        gradient.addColorStop(0, sourceNode.color || "#00E5FF");
        gradient.addColorStop(1, targetNode.color || "#D2BBFF");

        ctx.strokeStyle = isLinkActive ? gradient : "rgba(132, 147, 150, 0.25)";
        ctx.lineWidth = isLinkActive ? 2.5 * ((sourceNode.scale + targetNode.scale) / 2) : 1.2;
        ctx.stroke();

        // Draw relationship text label along the middle of the line
        if (isLinkActive || sourceNode.scale > 0.8) {
          const midX = (sourceNode.screenX + targetNode.screenX) / 2;
          const midY = (sourceNode.screenY + targetNode.screenY) / 2;
          ctx.fillStyle = isLinkActive ? "#00E5FF" : "rgba(255, 255, 255, 0.4)";
          ctx.font = `${Math.max(9, Math.round(11 * sourceNode.scale))}px monospace`;
          ctx.textAlign = "center";
          ctx.fillText(link.relation, midX, midY - 6);
        }
      });

      // Draw 3D Nodes
      projectedNodes.forEach((node) => {
        const radius = Math.max(8, Math.round(18 * node.scale));
        const isSelected = selectedNodeId === node.id;
        const isHovered = hoveredNode?.id === node.id;

        // Outer glow
        const glowRadius = radius * (isSelected ? 3.0 : isHovered ? 2.3 : 1.6);
        const radialGlow = ctx.createRadialGradient(
          node.screenX,
          node.screenY,
          radius * 0.2,
          node.screenX,
          node.screenY,
          glowRadius
        );
        radialGlow.addColorStop(0, node.color || "#00E5FF");
        radialGlow.addColorStop(1, "rgba(0, 0, 0, 0)");
        ctx.fillStyle = radialGlow;
        ctx.beginPath();
        ctx.arc(node.screenX, node.screenY, glowRadius, 0, Math.PI * 2);
        ctx.fill();

        // Solid Node Circle
        ctx.beginPath();
        ctx.arc(node.screenX, node.screenY, radius, 0, Math.PI * 2);
        ctx.fillStyle = node.color || "#00E5FF";
        ctx.fill();
        ctx.lineWidth = isSelected || isHovered ? 3 : 1.5;
        ctx.strokeStyle = isSelected ? "#FFFFFF" : "rgba(255, 255, 255, 0.6)";
        ctx.stroke();

        // Node Label
        ctx.fillStyle = isSelected ? "#00E5FF" : isHovered ? "#FFFFFF" : "rgba(255, 255, 255, 0.85)";
        ctx.font = `${isSelected ? "bold " : ""}${Math.max(11, Math.round(13 * node.scale))}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(node.label, node.screenX, node.screenY + radius + 16);

        // Confidence Tag below Label
        ctx.fillStyle = "rgba(180, 200, 210, 0.65)";
        ctx.font = `${Math.max(9, Math.round(10 * node.scale))}px monospace`;
        ctx.fillText(
          `${node.type} (${Math.round(node.confidence * 100)}%)`,
          node.screenX,
          node.screenY + radius + 29
        );
      });

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, [initialNodes, initialLinks, selectedNodeId, hoveredNode]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    dragRef.current = {
      isDragging: true,
      startX: e.clientX,
      startY: e.clientY,
      lastYaw: rotRef.current.yaw,
      lastPitch: rotRef.current.pitch,
    };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (dragRef.current.isDragging) {
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;
      rotRef.current.yaw = dragRef.current.lastYaw + dx * 0.006;
      rotRef.current.pitch = Math.max(
        -Math.PI / 2 + 0.1,
        Math.min(Math.PI / 2 - 0.1, dragRef.current.lastPitch + dy * 0.006)
      );
    } else {
      // Check for hover
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const fov = 550;
      const cosY = Math.cos(rotRef.current.yaw);
      const sinY = Math.sin(rotRef.current.yaw);
      const cosP = Math.cos(rotRef.current.pitch);
      const sinP = Math.sin(rotRef.current.pitch);

      let found: Node3D | null = null;
      for (const n of initialNodes) {
        const x1 = n.x * cosY - n.z * sinY;
        const z1 = n.z * cosY + n.x * sinY;
        const y2 = n.y * cosP - z1 * sinP;
        const z2 = z1 * cosP + n.y * sinP;
        const scale = fov / (fov + z2 + 400);
        const screenX = centerX + x1 * scale;
        const screenY = centerY + y2 * scale;
        const radius = Math.max(12, Math.round(20 * scale));

        const dist = Math.hypot(mouseX - screenX, mouseY - screenY);
        if (dist <= radius) {
          found = n;
          break;
        }
      }
      setHoveredNode(found);
      setIsHovering(!!found);
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const wasDragging = dragRef.current.isDragging;
    dragRef.current.isDragging = false;

    // If mouse didn't move much, treat as click on node
    if (wasDragging && Math.hypot(e.clientX - dragRef.current.startX, e.clientY - dragRef.current.startY) < 5) {
      if (hoveredNode && onSelectNode) {
        onSelectNode(hoveredNode);
      }
    }
  };

  return (
    <div className="relative w-full h-full overflow-hidden">
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        className={`w-full h-full transition-cursor ${
          dragRef.current.isDragging
            ? "cursor-grabbing"
            : isHovering
            ? "cursor-pointer"
            : "cursor-grab"
        }`}
      />
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2 bg-surface-container-high/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-outline-variant/30 text-xs font-mono text-on-surface-variant">
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
        3D Engine Active &bull; Drag to Rotate &bull; Click Node to Inspect
        <button
          onClick={() => {
            rotRef.current.autoRotate = !rotRef.current.autoRotate;
          }}
          className="ml-2 px-2 py-0.5 bg-primary/20 hover:bg-primary/30 text-primary font-bold rounded transition-colors"
        >
          {rotRef.current.autoRotate ? "Pause Orbit" : "Auto Orbit"}
        </button>
      </div>
    </div>
  );
}
