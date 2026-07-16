"use client";

import React, { useEffect, useRef } from "react";

export default function Aurora3DParticles() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let angle = 0;

    const resize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      } else {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
      }
    };
    resize();
    window.addEventListener("resize", resize);

    // Create 3D particles sphere/network
    const particleCount = 110;
    const particles: { x: number; y: number; z: number; size: number; color: string }[] = [];
    const colors = ["#00E5FF", "#D2BBFF", "#6FFBBE", "#3E517A"];

    for (let i = 0; i < particleCount; i++) {
      // Golden spiral distribution on sphere
      const phi = Math.acos(1 - 2 * (i + 0.5) / particleCount);
      const theta = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
      const radius = 280 + Math.random() * 80;

      particles.push({
        x: radius * Math.sin(phi) * Math.cos(theta),
        y: radius * Math.sin(phi) * Math.sin(theta),
        z: radius * Math.cos(phi),
        size: 1.5 + Math.random() * 2.5,
        color: colors[i % colors.length],
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const fov = 500;

      angle += 0.0035;
      const cosA = Math.cos(angle);
      const sinA = Math.sin(angle);
      const cosP = Math.cos(angle * 0.4);
      const sinP = Math.sin(angle * 0.4);

      // Project particles
      const projected = particles.map((p) => {
        const x1 = p.x * cosA - p.z * sinA;
        const z1 = p.z * cosA + p.x * sinA;
        const y2 = p.y * cosP - z1 * sinP;
        const z2 = z1 * cosP + p.y * sinP;

        const scale = fov / (fov + z2 + 400);
        const screenX = centerX + x1 * scale;
        const screenY = centerY + y2 * scale;

        return { ...p, screenX, screenY, scale, z2 };
      });

      // Sort back-to-front
      projected.sort((a, b) => b.z2 - a.z2);

      // Draw faint connections between nearby particles
      ctx.lineWidth = 0.8;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const dist = Math.hypot(projected[i].screenX - projected[j].screenX, projected[i].screenY - projected[j].screenY);
          if (dist < 110) {
            const alpha = (1 - dist / 110) * 0.18 * ((projected[i].scale + projected[j].scale) / 2);
            ctx.strokeStyle = `rgba(0, 229, 255, ${alpha.toFixed(3)})`;
            ctx.beginPath();
            ctx.moveTo(projected[i].screenX, projected[i].screenY);
            ctx.lineTo(projected[j].screenX, projected[j].screenY);
            ctx.stroke();
          }
        }
      }

      // Draw particles
      projected.forEach((p) => {
        const r = Math.max(1, p.size * p.scale);
        ctx.beginPath();
        ctx.arc(p.screenX, p.screenY, r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();

        if (p.scale > 0.9) {
          const glow = ctx.createRadialGradient(p.screenX, p.screenY, 0, p.screenX, p.screenY, r * 4);
          glow.addColorStop(0, p.color);
          glow.addColorStop(1, "rgba(0,0,0,0)");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(p.screenX, p.screenY, r * 4, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
      <canvas ref={canvasRef} className="w-full h-full opacity-65" />
    </div>
  );
}
