import { create } from 'zustand';

type Theme = 'dark' | 'light';

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>((set, get) => {
  // Read initial theme from localStorage or default to system/dark preference
  const getInitialTheme = (): Theme => {
    const saved = localStorage.getItem('repolens-theme') as Theme;
    if (saved === 'dark' || saved === 'light') return saved;
    return 'dark'; // Dark theme is default
  };

  const initialTheme = getInitialTheme();
  
  // Set class on document element immediately
  if (initialTheme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  return {
    theme: initialTheme,
    setTheme: (theme) => {
      localStorage.setItem('repolens-theme', theme);
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      set({ theme });
    },
    toggleTheme: () => {
      const nextTheme = get().theme === 'dark' ? 'light' : 'dark';
      get().setTheme(nextTheme);
    },
  };
});
