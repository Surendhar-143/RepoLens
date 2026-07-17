import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  notifications: Array<{ id: string; message: string; type: 'info' | 'success' | 'warning' | 'error' }>;
  addNotification: (message: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
  dismissNotification: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  notifications: [],
  addNotification: (message, type = 'info') => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      notifications: [...state.notifications, { id, message, type }],
    }));
    // Auto dismiss after 4 seconds
    setTimeout(() => {
      set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
      }));
    }, 4000);
  },
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
