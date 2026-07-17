import { create } from 'zustand';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  github_id?: string;
  github_username?: string;
  username?: string;
  avatar_url?: string;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: UserProfile) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  const token = localStorage.getItem('repolens-token');
  const userString = localStorage.getItem('repolens-user');
  let user: UserProfile | null = null;
  
  if (userString) {
    try {
      user = JSON.parse(userString);
    } catch {
      localStorage.removeItem('repolens-user');
    }
  }

  return {
    token,
    user,
    isAuthenticated: !!token,
    setAuth: (token, user) => {
      localStorage.setItem('repolens-token', token);
      localStorage.setItem('repolens-user', JSON.stringify(user));
      set({ token, user, isAuthenticated: true });
    },
    clearAuth: () => {
      localStorage.removeItem('repolens-token');
      localStorage.removeItem('repolens-user');
      set({ token: null, user: null, isAuthenticated: false });
    },
  };
});
