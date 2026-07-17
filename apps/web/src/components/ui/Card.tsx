import React, { HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Card: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => {
  return (
    <div
      className={twMerge(
        clsx('rounded-xl border border-border bg-card text-card-foreground shadow-xs glass-panel', className)
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('flex flex-col space-y-1.5 p-6', className))} {...props}>
      {children}
    </div>
  );
};

export const CardTitle: React.FC<HTMLAttributes<HTMLHeadingElement>> = ({ className, children, ...props }) => {
  return (
    <h3 className={twMerge(clsx('font-semibold leading-none tracking-tight font-display text-lg text-foreground', className))} {...props}>
      {children}
    </h3>
  );
};

export const CardDescription: React.FC<HTMLAttributes<HTMLParagraphElement>> = ({ className, children, ...props }) => {
  return (
    <p className={twMerge(clsx('text-sm text-muted-foreground', className))} {...props}>
      {children}
    </p>
  );
};

export const CardContent: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('p-6 pt-0', className))} {...props}>
      {children}
    </div>
  );
};

export const CardFooter: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => {
  return (
    <div className={twMerge(clsx('flex items-center p-6 pt-0 border-t border-border/40 mt-4', className))} {...props}>
      {children}
    </div>
  );
};
