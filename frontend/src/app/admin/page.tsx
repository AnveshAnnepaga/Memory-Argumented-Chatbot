"use client";

import React, { useState, useEffect } from "react";

export default function AdminConsolePage() {
  const [latencies, setLatencies] = useState({
    knowledge: 42,
    graph: 156,
    memory: 12,
    reasoning: 1240,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setLatencies((prev) => ({
        knowledge: Math.max(30, prev.knowledge + (Math.floor(Math.random() * 5) - 2)),
        graph: Math.max(130, prev.graph + (Math.floor(Math.random() * 7) - 3)),
        memory: Math.max(8, prev.memory + (Math.floor(Math.random() * 3) - 1)),
        reasoning: Math.max(900, prev.reasoning + (Math.floor(Math.random() * 21) - 10)),
      }));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="pl-64 pt-16 min-h-screen bg-background text-on-surface flex flex-col pb-24">
      {/* Top Header Bar */}
      <header className="fixed top-0 left-64 right-0 z-50 h-16 flex justify-between items-center px-lg backdrop-blur-xl bg-surface/30 border-b border-outline-variant/20">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[24px]">admin_panel_settings</span>
          <h2 className="text-headline-md font-headline-md font-bold text-on-surface">System Admin &amp; Orchestration Console</h2>
        </div>
        <div className="flex items-center gap-md">
          <span className="text-label-md px-3 py-1 bg-tertiary/10 text-tertiary border border-tertiary/20 rounded-full font-bold uppercase">
            SOC 2 Type II Certified
          </span>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            notifications
          </button>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
            contrast
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-lg space-y-lg max-w-[1600px] mx-auto w-full">
        {/* Global Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-lg">
          <div className="glass-surface p-lg rounded-xl flex flex-col gap-sm relative overflow-hidden border border-outline-variant/20 shadow-lg">
            <div className="absolute top-0 right-0 w-24 h-24 bg-primary-container/5 rounded-full -mr-8 -mt-8"></div>
            <span className="text-label-md font-label-md text-on-surface-variant">Active Enterprise Users</span>
            <div className="text-headline-lg font-headline-lg text-primary font-bold">12,842</div>
            <div className="flex items-center gap-xs text-tertiary">
              <span className="material-symbols-outlined text-[16px]">trending_up</span>
              <span className="text-label-md font-label-md">+4.2% from last hour</span>
            </div>
          </div>
          <div className="glass-surface p-lg rounded-xl flex flex-col gap-sm border border-outline-variant/20 shadow-lg">
            <span className="text-label-md font-label-md text-on-surface-variant">LangGraph Workflows</span>
            <div className="text-headline-lg font-headline-lg text-primary font-bold">452,109</div>
            <div className="flex items-center gap-xs text-tertiary">
              <span className="material-symbols-outlined text-[16px]">trending_up</span>
              <span className="text-label-md font-label-md">+12k queries today</span>
            </div>
          </div>
          <div className="glass-surface p-lg rounded-xl flex flex-col gap-sm border border-outline-variant/20 shadow-lg">
            <span className="text-label-md font-label-md text-on-surface-variant">Vector + Graph Index</span>
            <div className="text-headline-lg font-headline-lg text-primary font-bold">1.4 TB</div>
            <div className="flex items-center gap-xs text-on-surface-variant opacity-70">
              <span className="material-symbols-outlined text-[16px]">storage</span>
              <span className="text-label-md font-label-md">82% capacity allocated</span>
            </div>
          </div>
          <div className="glass-surface p-lg rounded-xl flex flex-col gap-sm border border-outline-variant/20 shadow-lg">
            <span className="text-label-md font-label-md text-on-surface-variant">Global Pipeline Uptime</span>
            <div className="text-headline-lg font-headline-lg text-tertiary font-bold">100.0%</div>
            <div className="flex items-center gap-xs text-tertiary">
              <span className="material-symbols-outlined text-[16px]">check_circle</span>
              <span className="text-label-md font-label-md">All 6 layers healthy</span>
            </div>
          </div>
        </div>

        {/* Engine Status Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg">
          {/* Engine Cards (8 cols) */}
          <div className="md:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-lg">
            {/* Knowledge Engine */}
            <div className="glass-surface p-lg rounded-xl flex flex-col gap-md border-l-4 border-l-primary-container border border-outline-variant/20 shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-headline-md font-headline-md text-primary font-bold">Knowledge Engine</h3>
                  <p className="text-body-sm font-body-sm text-on-surface-variant">Hybrid RAG &amp; Cross-Encoder</p>
                </div>
                <span className="px-md py-1 bg-tertiary/10 text-tertiary rounded-full text-label-md font-bold">ONLINE</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant opacity-70">Avg Latency</span>
                <span className="font-mono-code text-primary-container font-bold">{latencies.knowledge}ms</span>
              </div>
              <details className="group cursor-pointer">
                <summary className="list-none flex items-center gap-xs text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[18px] group-open:rotate-180 transition-transform">
                    expand_more
                  </span>
                  Show technical details
                </summary>
                <div className="mt-md p-md bg-surface-container-lowest rounded-lg font-mono-code text-[12px] space-y-1 border border-outline-variant/20">
                  <div className="flex justify-between"><span className="opacity-60">Index Size:</span> <span className="font-bold">4.2M vectors</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Throughput:</span> <span className="font-bold">850 req/s</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Error Rate:</span> <span className="text-tertiary font-bold">0.000%</span></div>
                </div>
              </details>
            </div>

            {/* Graph Engine */}
            <div className="glass-surface p-lg rounded-xl flex flex-col gap-md border-l-4 border-l-secondary border border-outline-variant/20 shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-headline-md font-headline-md text-secondary font-bold">Graph Engine</h3>
                  <p className="text-body-sm font-body-sm text-on-surface-variant">Neo4j GraphRAG Cluster</p>
                </div>
                <span className="px-md py-1 bg-tertiary/10 text-tertiary rounded-full text-label-md font-bold">ONLINE</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant opacity-70">Avg Latency</span>
                <span className="font-mono-code text-secondary font-bold">{latencies.graph}ms</span>
              </div>
              <details className="group cursor-pointer">
                <summary className="list-none flex items-center gap-xs text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[18px] group-open:rotate-180 transition-transform">
                    expand_more
                  </span>
                  Show technical details
                </summary>
                <div className="mt-md p-md bg-surface-container-lowest rounded-lg font-mono-code text-[12px] space-y-1 border border-outline-variant/20">
                  <div className="flex justify-between"><span className="opacity-60">Nodes:</span> <span className="font-bold">12.8M entities</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Edges:</span> <span className="font-bold">156M relations</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Graph Hop Speed:</span> <span className="text-tertiary font-bold">99.4%</span></div>
                </div>
              </details>
            </div>

            {/* Memory Engine */}
            <div className="glass-surface p-lg rounded-xl flex flex-col gap-md border-l-4 border-l-primary-fixed-dim border border-outline-variant/20 shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-headline-md font-headline-md text-primary-fixed-dim font-bold">Memory Engine</h3>
                  <p className="text-body-sm font-body-sm text-on-surface-variant">PostgreSQL Long-Term Store</p>
                </div>
                <span className="px-md py-1 bg-tertiary/10 text-tertiary rounded-full text-label-md font-bold">ONLINE</span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant opacity-70">Avg Latency</span>
                <span className="font-mono-code text-primary-fixed-dim font-bold">{latencies.memory}ms</span>
              </div>
              <details className="group cursor-pointer">
                <summary className="list-none flex items-center gap-xs text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[18px] group-open:rotate-180 transition-transform">
                    expand_more
                  </span>
                  Show technical details
                </summary>
                <div className="mt-md p-md bg-surface-container-lowest rounded-lg font-mono-code text-[12px] space-y-1 border border-outline-variant/20">
                  <div className="flex justify-between"><span className="opacity-60">Active Profiles:</span> <span className="font-bold">45.1k</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Fact Extraction:</span> <span className="font-bold">Instant</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Storage Shards:</span> <span className="font-bold">4.8 TB</span></div>
                </div>
              </details>
            </div>

            {/* Reasoning Engine */}
            <div className="glass-surface p-lg rounded-xl flex flex-col gap-md border-l-4 border-l-tertiary border border-outline-variant/20 shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-headline-md font-headline-md text-tertiary font-bold">Reasoning Engine</h3>
                  <p className="text-body-sm font-body-sm text-on-surface-variant">LangGraph Router + Groq LPU</p>
                </div>
                <span className="px-md py-1 bg-primary/10 text-primary rounded-full text-label-md font-bold animate-pulse">
                  OPTIMAL
                </span>
              </div>
              <div className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant opacity-70">Avg Latency</span>
                <span className="font-mono-code text-tertiary font-bold">{latencies.reasoning}ms</span>
              </div>
              <details className="group cursor-pointer">
                <summary className="list-none flex items-center gap-xs text-label-md font-label-md text-on-surface-variant hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[18px] group-open:rotate-180 transition-transform">
                    expand_more
                  </span>
                  Show technical details
                </summary>
                <div className="mt-md p-md bg-surface-container-lowest rounded-lg font-mono-code text-[12px] space-y-1 border border-outline-variant/20">
                  <div className="flex justify-between"><span className="opacity-60">LPU Load:</span> <span className="text-tertiary font-bold">42.4%</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Tokens/sec:</span> <span className="font-bold">14.2M</span></div>
                  <div className="flex justify-between"><span className="opacity-60">Queue Depth:</span> <span className="font-bold">0</span></div>
                </div>
              </details>
            </div>
          </div>

          {/* Audit Log Feed (4 cols) */}
          <div className="md:col-span-4 flex flex-col glass-surface rounded-xl overflow-hidden border border-outline-variant/20 shadow-xl">
            <div className="p-md border-b border-outline-variant/10 flex justify-between items-center bg-surface-container-low/50">
              <span className="text-label-md font-label-md text-on-surface font-bold">Real-Time Audit Log</span>
              <span className="text-label-md font-label-md text-primary cursor-pointer hover:underline">Export CSV</span>
            </div>
            <div className="flex-1 p-md space-y-md overflow-y-auto custom-scrollbar max-h-[480px]">
              <div className="flex gap-md group">
                <div className="flex flex-col items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-primary mt-1.5"></div>
                  <div className="w-[1px] flex-1 bg-outline-variant/30"></div>
                </div>
                <div className="flex flex-col pb-sm">
                  <span className="text-label-md font-label-md text-on-surface-variant opacity-60">Just now</span>
                  <p className="text-body-sm font-body-sm text-on-surface">
                    Architect <span className="text-primary font-bold">@anvesh4</span> verified Milestone 15 production UI.
                  </p>
                </div>
              </div>

              <div className="flex gap-md group">
                <div className="flex flex-col items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-tertiary mt-1.5"></div>
                  <div className="w-[1px] flex-1 bg-outline-variant/30"></div>
                </div>
                <div className="flex flex-col pb-sm">
                  <span className="text-label-md font-label-md text-on-surface-variant opacity-60">2 minutes ago</span>
                  <p className="text-body-sm font-body-sm text-on-surface">
                    LangGraph state graph initialized with defensive <span className="text-tertiary font-mono-code">retrieved_chunks</span> serialization.
                  </p>
                </div>
              </div>

              <div className="flex gap-md group">
                <div className="flex flex-col items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-secondary mt-1.5"></div>
                  <div className="w-[1px] flex-1 bg-outline-variant/30"></div>
                </div>
                <div className="flex flex-col pb-sm">
                  <span className="text-label-md font-label-md text-on-surface-variant opacity-60">15 minutes ago</span>
                  <p className="text-body-sm font-body-sm text-on-surface">
                    Automatic backup of <span className="text-secondary font-bold">&quot;Enterprise_Graph_v15&quot;</span> completed successfully.
                  </p>
                </div>
              </div>

              <div className="flex gap-md group">
                <div className="flex flex-col items-center gap-sm">
                  <div className="w-2.5 h-2.5 rounded-full bg-primary-container mt-1.5"></div>
                  <div className="w-[1px] flex-1 bg-outline-variant/30"></div>
                </div>
                <div className="flex flex-col pb-sm">
                  <span className="text-label-md font-label-md text-on-surface-variant opacity-60">1 hour ago</span>
                  <p className="text-body-sm font-body-sm text-on-surface">
                    System Update: Evaluation &amp; Observability telemetry node synced to sub-400ms SLA.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* User Management Table */}
        <div className="glass-surface rounded-xl overflow-hidden border border-outline-variant/20 shadow-xl">
          <div className="p-lg border-b border-outline-variant/10 flex justify-between items-center bg-surface-container-low/30">
            <h3 className="text-headline-md font-headline-md text-on-surface font-bold">RBAC &amp; User Access Management</h3>
            <div className="flex gap-md">
              <button className="px-md py-sm bg-surface-container-high hover:bg-surface-variant transition-colors border border-outline-variant/20 text-on-surface text-label-md font-label-md rounded-lg flex items-center gap-xs cursor-pointer">
                <span className="material-symbols-outlined text-[18px]">filter_list</span> Filter
              </button>
              <button
                onClick={() => alert("Simulating enterprise SSO invite dialog...")}
                className="px-md py-sm bg-primary-container text-on-primary-container hover:opacity-90 transition-all font-bold text-label-md font-label-md rounded-lg flex items-center gap-xs cursor-pointer shadow-md"
              >
                <span className="material-symbols-outlined text-[18px]">person_add</span> Invite User
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead className="bg-surface-container-low/50">
                <tr>
                  <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                    Name / ID
                  </th>
                  <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                    Role &amp; Layer Access
                  </th>
                  <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                    Last Active
                  </th>
                  <th className="px-lg py-md text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                <tr className="hover:bg-surface-variant/20 transition-colors">
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-md">
                      <div className="w-9 h-9 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs shadow">
                        AM
                      </div>
                      <div>
                        <div className="text-body-sm font-bold text-on-surface">Anvesh Mishra</div>
                        <div className="text-[12px] text-on-surface-variant opacity-70 font-mono-code">UUID: SYS-ARCHITECT-01</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-lg py-md">
                    <span className="px-2.5 py-1 bg-primary-container/20 text-primary border border-primary/30 text-[11px] font-bold rounded">
                      Super Admin (All 6 Layers)
                    </span>
                  </td>
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></div>
                      <span className="text-body-sm font-bold text-tertiary">Active Now</span>
                    </div>
                  </td>
                  <td className="px-lg py-md text-body-sm text-on-surface-variant">Current Session</td>
                  <td className="px-lg py-md">
                    <button className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
                      <span className="material-symbols-outlined">more_horiz</span>
                    </button>
                  </td>
                </tr>

                <tr className="hover:bg-surface-variant/20 transition-colors">
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-md">
                      <div className="w-9 h-9 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-bold text-xs shadow">
                        EK
                      </div>
                      <div>
                        <div className="text-body-sm font-bold text-on-surface">Elena Kovac</div>
                        <div className="text-[12px] text-on-surface-variant opacity-70 font-mono-code">UUID: 14-802-Y</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-lg py-md">
                    <span className="px-2.5 py-1 bg-secondary-container/20 text-secondary border border-secondary/30 text-[11px] font-bold rounded">
                      Data &amp; Graph Engineer
                    </span>
                  </td>
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-on-surface-variant/50"></div>
                      <span className="text-body-sm text-on-surface-variant">Idle</span>
                    </div>
                  </td>
                  <td className="px-lg py-md text-body-sm text-on-surface-variant">14 hours ago</td>
                  <td className="px-lg py-md">
                    <button className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
                      <span className="material-symbols-outlined">more_horiz</span>
                    </button>
                  </td>
                </tr>

                <tr className="hover:bg-surface-variant/20 transition-colors">
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-md">
                      <div className="w-9 h-9 rounded-full bg-error-container/30 flex items-center justify-center text-error font-bold text-xs shadow">
                        RB
                      </div>
                      <div>
                        <div className="text-body-sm font-bold text-on-surface">Rick Burke</div>
                        <div className="text-[12px] text-on-surface-variant opacity-70 font-mono-code">UUID: 99-122-Z</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-lg py-md">
                    <span className="px-2.5 py-1 bg-surface-container-highest text-on-surface-variant text-[11px] font-bold rounded border border-outline-variant/30">
                      External Auditor
                    </span>
                  </td>
                  <td className="px-lg py-md">
                    <div className="flex items-center gap-1.5 text-error">
                      <span className="material-symbols-outlined text-[14px]">lock</span>
                      <span className="text-body-sm font-bold">Suspended</span>
                    </div>
                  </td>
                  <td className="px-lg py-md text-body-sm text-on-surface-variant">3 days ago</td>
                  <td className="px-lg py-md">
                    <button className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
                      <span className="material-symbols-outlined">more_horiz</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
}
