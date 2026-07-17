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

export type MessageMetadata = Record<string, unknown>;
export type MessageEvaluation = Record<string, unknown>;

export interface FileAttachment {
  fileId: string;
  filename: string;
  mimeType: string;
  sizeBytes: number;
  type: 'pdf' | 'docx' | 'image' | 'other';
}

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  attachments?: FileAttachment[];
  metadata?: MessageMetadata;
  evaluation?: MessageEvaluation;
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
  updateLastAssistantMessage: (
    updater: (
      prevText: string,
      prevSteps?: ChatStep[]
    ) => {
      text: string;
      steps?: ChatStep[];
      evaluation?: MessageEvaluation;
      citations?: CitationItem[];
      metadata?: MessageMetadata;
    }
  ) => void;
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

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  activeConversationId: '',
  isStreaming: false,
  activeSteps: [],
  conversations: [],

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
