import type { LatencyBreakdown as LatencyType } from '../../types/query';
import { formatMs } from '../../utils/formatters';

interface LatencyBreakdownProps {
  latency: LatencyType;
}

const stages = [
  { key: 'embedding_and_dense_ms' as const, label: 'Embed + Dense', color: 'bg-info' },
  { key: 'sparse_ms' as const, label: 'Sparse', color: 'bg-secondary' },
  { key: 'reranking_ms' as const, label: 'Rerank', color: 'bg-warning' },
  { key: 'generation_ms' as const, label: 'Generate', color: 'bg-accent' },
];

export default function LatencyBreakdown({ latency }: LatencyBreakdownProps) {
  const computedTotal = (latency.embedding_and_dense_ms ?? 0) + (latency.sparse_ms ?? 0)
    + (latency.reranking_ms ?? 0) + (latency.generation_ms ?? 0);
  const totalMs = latency.total_ms || computedTotal;
  const total = totalMs || 1;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">
          Pipeline Latency
        </h4>
        <span className="text-xs font-mono text-text-muted dark:text-dark-text-muted">
          {formatMs(totalMs)}
        </span>
      </div>

      {/* Stacked Bar */}
      <div className="flex h-6 rounded-lg overflow-hidden bg-surface dark:bg-dark-surface-alt">
        {stages.map(({ key, color }) => {
          const ms = latency[key] ?? 0;
          const pct = (ms / total) * 100;
          if (pct < 1) return null;
          return (
            <div
              key={key}
              className={`${color} opacity-80 hover:opacity-100 transition-opacity`}
              style={{ width: `${pct}%` }}
              title={`${stages.find((s) => s.key === key)?.label}: ${formatMs(ms)}`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4">
        {stages.map(({ key, label, color }) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-sm ${color} opacity-80`} />
            <span className="text-xs text-text-muted dark:text-dark-text-muted">
              {label}: {formatMs(latency[key] ?? 0)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
