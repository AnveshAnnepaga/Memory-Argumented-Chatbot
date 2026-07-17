"use client";

import React, { useEffect, useRef } from "react";

type Particle = {
  x: number;
  y: number;
  z: number;
  size: number;
  color: string;
};

export default function Aurora3DParticles() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId = 0;
    let angle = 0;
    const particleCount = 110;
    const colors = ["#00E5FF", "#D2BBFF", "#6FFFBE", "#3E517A"];
    let particles: Particle[] = [];

    const getSize = () => {
      const parent = canvas.parentElement;
      const w = parent ? parent.clientWidth : window.innerWidth;
      const h = parent ? parent.clientHeight : window.innerHeight;
      return { w: Math.max(1, w), h: Math.max(1, h) };
    };

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      const { w, h } = getSize();
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Rebuild particle sphere scaled to current viewport so it always fits.
      const baseRadius = Math.min(w, h) * 0.55;
      const radiusJitter = Math.min(w, h) * 0.12;
      particles = [];
      for (let i = 0; i < particleCount; i++) {
        const phi = Math.acos(1 - 2 * (i + 0.5) / particleCount);
        const theta = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
        const radius = baseRadius + Math.random() * radiusJitter;
        particles.push({
          x: radius * Math.sin(phi) * Math.cos(theta),
          y: radius * Math.sin(phi) * Math.sin(theta),
          z: radius * Math.cos(phi),
          size: 1.2 + Math.random() * 2.2,
          color: colors[i % colors.length],
        });
      }
    };

    resize();
    window.addEventListener("resize", resize);

    const render = () => {
      const { w, h } = getSize();
      ctx.clearRect(0, 0, w, h);
      const centerX = w / 2;
      const centerY = h / 2;
      const fov = 500;
      const depthOffset = Math.min(w, h) * 1.1;

      angle += 0.0035;
      const cosA = Math.cos(angle);
      const sinA = Math.sin(angle);
      const cosP = Math.cos(angle * 0.4);
      const sinP = Math.sin(angle * 0.4);

      const projected = particles.map((p) => {
        const x1 = p.x * cosA - p.z * sinA;
        const z1 = p.z * cosA + p.x * sinA;
        const y2 = p.y * cosP - z1 * sinP;
        const z2 = z1 * cosP + p.y * sinP;

        const scale = fov / (fov + z2 + depthOffset);
        const screenX = centerX + x1 * scale;
        const screenY = centerY + y2 * scale;

        return { ...p, screenX, screenY, scale, z2 };
      });

      // Back-to-front so closer particles overlay farther ones.
      projected.sort((a, b) => b.z2 - a.z2);

      ctx.lineWidth = 0.8;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const a = projected[i];
          const b = projected[j];
          const dist = Math.hypot(a.screenX - b.screenX, a.screenY - b.screenY);
          if (dist < 110) {
            const alpha = (1 - dist / 110) * 0.18 * ((a.scale + b.scale) / 2);
            ctx.strokeStyle = `rgba(0, 229, 255, ${alpha.toFixed(3)})`;
            ctx.beginPath();
            ctx.moveTo(a.screenX, a.screenY);
            ctx.lineTo(b.screenX, b.screenY);
            ctx.stroke();
          }
        }
      }

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
      <canvas ref={canvasRef} className="block w-full h-full opacity-65" />
    </div>
  );
}
