import { create } from 'zustand';

export interface ChatStep {
  node: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  label: string;
}

export interface CitationItem {
  source: string;
  snippet: string;
  score?: number;
  type?: 'RAG' | 'GRAPH' | 'MEMORY';
}

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  metadata?: any;
  evaluation?: any;
  citations?: CitationItem[];
  steps?: ChatStep[];
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  pinned: boolean;
  messageCount: number;
}

interface ChatState {
  messages: Message[];
  activeConversationId: string;
  isStreaming: boolean;
  activeSteps: ChatStep[];
  conversations: Conversation[];
  
  // Actions
  addMessage: (msg: Message) => void;
  updateLastAssistantMessage: (updater: (prevText: string, prevSteps?: ChatStep[]) => { text: string; steps?: ChatStep[]; evaluation?: any; citations?: CitationItem[]; metadata?: any }) => void;
  setActiveSteps: (steps: ChatStep[]) => void;
  setIsStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
  
  // Conversation management
  setActiveConversationId: (id: string) => void;
  createConversation: (title?: string) => string;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, newTitle: string) => void;
  togglePinConversation: (id: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [
    {
      id: 'welcome-msg',
      sender: 'assistant',
      text: "👋 Welcome to **Antigravity Intelligence Engine v15.0**.\n\nI am connected to all 6 backend intelligence layers:\n- **LangGraph Orchestration** (Reasoning Engine)\n- **Hybrid RAG** (Pinecone + BM25 + Cross-Encoder)\n- **GraphRAG** (Neo4j Knowledge Graph)\n- **Long-Term Memory** (PostgreSQL User Profile & Semantic Facts)\n- **Tool Execution Framework** (External APIs & Math Engines)\n- **Observability Platform** (Real-Time Hallucination & Latency Evaluation)\n\nAsk me anything or test complex reasoning below!",
      timestamp: new Date().toISOString(),
    }
  ],
  activeConversationId: 'default-session',
  isStreaming: false,
  activeSteps: [],
  conversations: [
    {
      id: 'default-session',
      title: 'General Exploration & Architecture',
      createdAt: new Date().toISOString(),
      pinned: true,
      messageCount: 1,
    },
    {
      id: 'rag-test-session',
      title: 'FastAPI & RAG Performance Test',
      createdAt: new Date(Date.now() - 3600000).toISOString(),
      pinned: false,
      messageCount: 4,
    },
    {
      id: 'graph-test-session',
      title: 'Neo4j Graph Traversal Analysis',
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      pinned: false,
      messageCount: 2,
    }
  ],

  addMessage: (msg) => set((state) => ({
    messages: [...state.messages, msg],
    conversations: state.conversations.map(c => 
      c.id === state.activeConversationId 
        ? { ...c, messageCount: c.messageCount + 1 } 
        : c
    )
  })),

  updateLastAssistantMessage: (updater) => set((state) => {
    const msgs = [...state.messages];
    const lastIdx = msgs.length - 1;
    if (lastIdx >= 0 && msgs[lastIdx].sender === 'assistant') {
      const current = msgs[lastIdx];
      const updated = updater(current.text, current.steps);
      msgs[lastIdx] = {
        ...current,
        text: updated.text,
        steps: updated.steps || current.steps,
        evaluation: updated.evaluation || current.evaluation,
        citations: updated.citations || current.citations,
        metadata: updated.metadata || current.metadata,
      };
    }
    return { messages: msgs };
  }),

  setActiveSteps: (steps) => set({ activeSteps: steps }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  clearMessages: () => set({ messages: [] }),

  setActiveConversationId: (id) => set({ activeConversationId: id }),
  createConversation: (title = 'New Intelligence Session') => {
    const id = `session-${Date.now()}`;
    const newConv: Conversation = {
      id,
      title,
      createdAt: new Date().toISOString(),
      pinned: false,
      messageCount: 0,
    };
    set((state) => ({
      conversations: [newConv, ...state.conversations],
      activeConversationId: id,
      messages: [],
    }));
    return id;
  },
  deleteConversation: (id) => set((state) => ({
    conversations: state.conversations.filter((c) => c.id !== id),
    activeConversationId: state.activeConversationId === id 
      ? (state.conversations.find((c) => c.id !== id)?.id || 'default-session')
      : state.activeConversationId,
  })),
  renameConversation: (id, newTitle) => set((state) => ({
    conversations: state.conversations.map((c) => c.id === id ? { ...c, title: newTitle } : c)
  })),
  togglePinConversation: (id) => set((state) => ({
    conversations: state.conversations.map((c) => c.id === id ? { ...c, pinned: !c.pinned } : c)
  })),
}));
