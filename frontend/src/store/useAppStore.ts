import { create } from 'zustand';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'ENGINEER' | 'USER';
  avatarUrl?: string;
  created_at?: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
}

interface AppState {
  sidebarOpen: boolean;
  activeTab: string;
  user: UserProfile | null;
  systemHealth: 'HEALTHY' | 'WARNING' | 'DEGRADED' | 'CRITICAL';
  notifications: Array<{ id: string; title: string; message: string; type: 'info' | 'success' | 'warning' | 'error'; time: string }>;

  // Auth state
  token: string | null;
  isAuthenticated: boolean;
  authUser: AuthUser | null;
  authModalOpen: boolean;

  // Conversation save counter (to trigger profile refresh)
  conversationSaveCount: number;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: string) => void;
  setSystemHealth: (health: 'HEALTHY' | 'WARNING' | 'DEGRADED' | 'CRITICAL') => void;
  addNotification: (notif: Omit<AppState['notifications'][0], 'id' | 'time'>) => void;
  removeNotification: (id: string) => void;

  // Auth actions
  setAuthModalOpen: (open: boolean) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  loadAuthFromStorage: () => Promise<void>;
  incrementConversationSaveCount: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

async function apiFetch(url: string, options: RequestInit = {}, timeoutMs = 30000, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      return res;
    } catch (err) {
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
        continue;
      }
      const msg = err instanceof Error ? err.message : String(err);
      throw new Error(`Failed to connect to ${url} — ${msg}`);
    } finally {
      clearTimeout(timeout);
    }
  }
  throw new Error(`Failed to connect to ${url} — max retries exceeded`);
}

function mapBackendUser(backendUser: AuthUser): UserProfile {
  return {
    id: backendUser.id,
    name: backendUser.full_name || backendUser.email.split('@')[0],
    email: backendUser.email,
    role: 'USER' as const,
    avatarUrl: undefined,
    created_at: backendUser.created_at,
  };
}

export const useAppStore = create<AppState>((set, get) => ({
  sidebarOpen: true,
  activeTab: 'chat',
  user: null,
  systemHealth: 'HEALTHY',
  notifications: [
    {
      id: 'notif-init',
      title: 'System Online',
      message: 'All intelligence layers connected and ready for high-throughput evaluation.',
      type: 'success',
      time: 'Just now',
    }
  ],

  token: null,
  isAuthenticated: false,
  authUser: null,
  authModalOpen: false,
  conversationSaveCount: 0,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSystemHealth: (health) => set({ systemHealth: health }),
  addNotification: (notif) => set((state) => ({
    notifications: [
      { ...notif, id: `notif-${Date.now()}`, time: 'Just now' },
      ...state.notifications.slice(0, 9)
    ]
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter((n) => n.id !== id)
  })),

  setAuthModalOpen: (open) => set({ authModalOpen: open }),

  login: async (email: string, password: string) => {
    try {
      const res = await apiFetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error?.message || err.detail || err.message || 'Login failed');
      }
      const data = await res.json();
      const token = data.access_token;
      localStorage.setItem('vyron_token', token);
      localStorage.setItem('vyron_refresh', data.refresh_token);
      set({
        token,
        isAuthenticated: true,
        authUser: data.user,
        user: mapBackendUser(data.user),
        authModalOpen: false,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      console.error('Login error:', message);
      throw err;
    }
  },

  register: async (email: string, password: string, fullName?: string) => {
    try {
      const res = await apiFetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error?.message || err.detail || err.message || 'Registration failed');
      }
      const data = await res.json();
      localStorage.setItem('vyron_token', data.access_token);
      localStorage.setItem('vyron_refresh', data.refresh_token);
      set({
        token: data.access_token,
        isAuthenticated: true,
        authUser: data.user,
        user: mapBackendUser(data.user),
        authModalOpen: false,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      console.error('Register error:', message);
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('vyron_token');
    localStorage.removeItem('vyron_refresh');
    set({
      token: null,
      isAuthenticated: false,
      authUser: null,
      user: null,
    });
  },

  incrementConversationSaveCount: () => set((state) => ({ conversationSaveCount: state.conversationSaveCount + 1 })),

  loadAuthFromStorage: async () => {
    const token = localStorage.getItem('vyron_token');
    if (!token) return;

    try {
      const res = await apiFetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!res.ok) {
        localStorage.removeItem('vyron_token');
        localStorage.removeItem('vyron_refresh');
        return;
      }
      const userData = await res.json();
      set({
        token,
        isAuthenticated: true,
        authUser: userData,
        user: mapBackendUser(userData),
      });
    } catch {
      localStorage.removeItem('vyron_token');
      localStorage.removeItem('vyron_refresh');
    }
  },
}));
