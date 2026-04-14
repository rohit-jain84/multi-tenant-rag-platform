import type { DocumentStatus } from '../../types/document';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';

const config: Record<DocumentStatus, { icon: typeof Clock; label: string; className: string }> = {
  queued: { icon: Clock, label: 'Queued', className: 'bg-info/10 text-info' },
  processing: { icon: Loader2, label: 'Processing', className: 'bg-warning/10 text-warning' },
  completed: { icon: CheckCircle2, label: 'Completed', className: 'bg-success/10 text-success' },
  failed: { icon: XCircle, label: 'Failed', className: 'bg-danger/10 text-danger' },
};

export default function StatusBadge({ status }: { status: DocumentStatus }) {
  const { icon: Icon, label, className } = config[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${className}`}>
      <Icon className={`h-3.5 w-3.5 ${status === 'processing' ? 'animate-spin' : ''}`} />
      {label}
    </span>
  );
}
