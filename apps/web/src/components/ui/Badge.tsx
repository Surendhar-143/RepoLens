import React, { HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'error';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-hidden focus:ring-2 focus:ring-ring focus:ring-offset-2';
  
  const variants = {
    default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
    secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
    outline: 'text-foreground border-border bg-transparent',
    success: 'border-transparent bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    warning: 'border-transparent bg-amber-500/10 text-amber-400 border border-amber-500/20',
    error: 'border-transparent bg-rose-500/10 text-rose-400 border border-rose-500/20',
  };

  return (
    <div
      className={twMerge(clsx(baseStyles, variants[variant], className))}
      {...props}
    >
      {children}
    </div>
  );
};
