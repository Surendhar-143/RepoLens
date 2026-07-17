import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface LoaderProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Loader: React.FC<LoaderProps> = ({ className, size = 'md' }) => {
  const sizes = {
    sm: 'h-4 w-4 stroke-2',
    md: 'h-8 w-8 stroke-2',
    lg: 'h-12 w-12 stroke-[2.5]',
  };

  return (
    <div className={twMerge(clsx('flex items-center justify-center', className))}>
      <svg
        className={twMerge(clsx('animate-spin text-muted-foreground', sizes[size]))}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-20"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-80"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
};
