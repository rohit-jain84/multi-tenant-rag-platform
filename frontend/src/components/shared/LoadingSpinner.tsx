import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  fullPage?: boolean;
}

export default function LoadingSpinner({ label, fullPage = false }: LoadingSpinnerProps) {
  const content = (
    <div className="flex flex-col items-center gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      {label && <p className="text-sm text-text-muted dark:text-dark-text-muted">{label}</p>}
    </div>
  );

  if (fullPage) {
    return <div className="flex items-center justify-center min-h-[400px]">{content}</div>;
  }

  return content;
}
