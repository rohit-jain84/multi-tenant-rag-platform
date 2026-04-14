import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}

export default function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-surface dark:bg-dark-surface-alt flex items-center justify-center mb-4">
        <Icon className="h-8 w-8 text-text-muted dark:text-dark-text-muted" />
      </div>
      <h3 className="text-lg font-semibold text-text dark:text-dark-text mb-1">{title}</h3>
      <p className="text-sm text-text-muted dark:text-dark-text-muted max-w-sm mb-4">
        {description}
      </p>
      {action}
    </div>
  );
}
