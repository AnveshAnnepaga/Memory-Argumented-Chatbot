import { create } from 'zustand';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'ENGINEER' | 'USER';
  avatarUrl?: string;
}

interface AppState {
  sidebarOpen: boolean;
  activeTab: string;
  user: UserProfile | null;
  systemHealth: 'HEALTHY' | 'WARNING' | 'DEGRADED' | 'CRITICAL';
  notifications: Array<{ id: string; title: string; message: string; type: 'info' | 'success' | 'warning' | 'error'; time: string }>;
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: string) => void;
  setSystemHealth: (health: 'HEALTHY' | 'WARNING' | 'DEGRADED' | 'CRITICAL') => void;
  addNotification: (notif: Omit<AppState['notifications'][0], 'id' | 'time'>) => void;
  removeNotification: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  activeTab: 'chat',
  user: {
    id: 'anvesh-01',
    name: 'Anvesh Mishra',
    email: 'anvesh@antigravity.ai',
    role: 'ADMIN',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&q=80',
  },
  systemHealth: 'HEALTHY',
  notifications: [
    {
      id: 'notif-init',
      title: 'Milestone 15 Online',
      message: 'All 6 intelligence layers connected and ready for high-throughput evaluation.',
      type: 'success',
      time: 'Just now',
    }
  ],

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
}));
