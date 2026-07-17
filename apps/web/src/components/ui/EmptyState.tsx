import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from './Card.tsx';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon,
  action,
}) => {
  return (
    <Card className="w-full flex items-center justify-center p-8 min-h-[300px] border-dashed">
      <CardContent className="flex flex-col items-center justify-center text-center space-y-4 max-w-md p-0">
        {Icon && (
          <div className="p-3 bg-[#a21caf]/10 border border-[#a21caf]/20 rounded-full text-[#a21caf]">
            <Icon className="h-8 w-8" />
          </div>
        )}
        <div className="space-y-2">
          <h3 className="text-xl font-semibold tracking-tight text-foreground font-display">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        {action && <div className="mt-2">{action}</div>}
      </CardContent>
    </Card>
  );
};
