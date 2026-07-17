import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useThemeStore } from '../../stores/theme.ts';
import { Button } from './Button.tsx';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="rounded-full w-8 h-8 flex items-center justify-center border border-border/30 hover:border-border/60"
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? (
        <Sun className="h-4 w-4 text-amber-400" />
      ) : (
        <Moon className="h-4 w-4 text-violet-400" />
      )}
    </Button>
  );
};
