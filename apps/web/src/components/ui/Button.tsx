import React, { ButtonHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 cursor-pointer rounded-md';
  
  const variants = {
    primary: 'bg-[#a21caf] text-white shadow-sm hover:bg-[#86198f] active:bg-[#701a75]',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-[#27272a] active:bg-[#1f1f23]',
    outline: 'border border-border bg-transparent hover:bg-secondary hover:text-secondary-foreground',
    ghost: 'hover:bg-secondary hover:text-secondary-foreground text-muted-foreground hover:text-foreground',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-red-700 active:bg-red-800',
  };

  const sizes = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-9 px-4 py-2 text-sm',
    lg: 'h-10 px-6 text-base',
    icon: 'h-9 w-9',
  };

  return (
    <button
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg
          className="mr-2 h-4 w-4 animate-spin text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : null}
      {children}
    </button>
  );
};
