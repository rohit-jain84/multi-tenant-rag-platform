import type { EvalRun } from '../../types/eval';
import Card from '../shared/Card';

interface ScoreCardsProps {
  metrics: EvalRun | null;
}

const metricConfig = [
  { key: 'context_recall' as const, label: 'Context Recall', target: 0.85, color: '#e94560' },
  { key: 'faithfulness' as const, label: 'Faithfulness', target: 0.80, color: '#0f3460' },
  { key: 'answer_relevancy' as const, label: 'Answer Relevancy', target: 0.75, color: '#3498db' },
  { key: 'context_precision' as const, label: 'Context Precision', target: 0.75, color: '#2ecc71' },
];

export default function ScoreCards({ metrics }: ScoreCardsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {metricConfig.map(({ key, label, target, color }) => {
        const value = metrics?.[key];
        const meetsTarget = value != null && value >= target;
        return (
          <Card key={key} accentColor={color}>
            <p className="text-xs font-medium text-text-muted dark:text-dark-text-muted uppercase tracking-wider mb-2">
              {label}
            </p>
            <p className="text-3xl font-bold" style={{ color }}>
              {value != null ? value.toFixed(3) : '—'}
            </p>
            <div className="flex items-center gap-1.5 mt-2">
              <div className={`w-2 h-2 rounded-full ${meetsTarget ? 'bg-success' : value != null ? 'bg-danger' : 'bg-border'}`} />
              <span className="text-xs text-text-muted dark:text-dark-text-muted">
                Target: {'>'}  {target}
              </span>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
