import type { ABComparisonResult } from '../../types/eval';

interface ABComparisonProps {
  data: ABComparisonResult[];
}

export default function ABComparison({ data }: ABComparisonProps) {
  if (data.length === 0) {
    return (
      <p className="text-sm text-text-muted dark:text-dark-text-muted py-4 text-center">
        No A/B comparison data available yet. Run an evaluation to generate comparison.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border dark:border-dark-border">
            <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Metric</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Hybrid</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Dense Only</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Improvement</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border dark:divide-dark-border">
          {data.map((row) => (
            <tr key={row.metric} className="hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors">
              <td className="py-3 px-4 text-sm font-medium text-text dark:text-dark-text">{row.metric}</td>
              <td className="py-3 px-4 text-sm text-right font-mono text-text-muted dark:text-dark-text-muted">{row.hybrid.toFixed(4)}</td>
              <td className="py-3 px-4 text-sm text-right font-mono text-text-muted dark:text-dark-text-muted">{row.dense_only.toFixed(4)}</td>
              <td className="py-3 px-4 text-sm text-right font-mono">
                <span className={row.improvement > 0 ? 'text-success' : row.improvement < 0 ? 'text-danger' : 'text-text-muted'}>
                  {row.improvement > 0 ? '+' : ''}{(row.improvement * 100).toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
