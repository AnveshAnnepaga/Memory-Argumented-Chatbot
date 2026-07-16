import type { Metadata } from "next";
import { Inter, Inter_Tight, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "../components/layout/Providers";
import { AppLayoutWrapper } from "../components/layout/AppLayoutWrapper";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const interTight = Inter_Tight({
  variable: "--font-inter-tight",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Antigravity AI | Enterprise AI Assistant & Production Studio",
  description: "Breathtaking Enterprise AI Platform by Anvesh Mishra featuring LangGraph Orchestration, Hybrid RAG, GraphRAG, Long-Term Memory, and Evaluation Observability.",
  keywords: ["FastAPI", "Next.js 15", "LangGraph", "GraphRAG", "Neo4j", "Pinecone", "Evaluation", "Observability", "Antigravity AI"],
  authors: [{ name: "Anvesh Mishra", url: "https://github.com/anvesh4" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${interTight.variable} ${jetbrainsMono.variable} dark antialiased`}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background text-on-surface selection:bg-primary-container/30 selection:text-primary">
        <Providers>
          <AppLayoutWrapper>
            {children}
          </AppLayoutWrapper>
        </Providers>
      </body>
    </html>
  );
}
