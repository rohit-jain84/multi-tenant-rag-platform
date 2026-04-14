import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface QuestionResult {
  question: string;
  context_recall?: number;
  faithfulness?: number;
  answer_relevancy?: number;
  context_precision?: number;
  [key: string]: unknown;
}

interface QuestionBreakdownProps {
  questions: QuestionResult[];
}

export default function QuestionBreakdown({ questions }: QuestionBreakdownProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (questions.length === 0) {
    return (
      <p className="text-sm text-text-muted dark:text-dark-text-muted py-4 text-center">
        No per-question evaluation data available yet.
      </p>
    );
  }

  const metricKeys = ['context_recall', 'faithfulness', 'answer_relevancy', 'context_precision'] as const;

  return (
    <div className="space-y-2">
      {questions.map((q, i) => (
        <div key={i} className="border border-border dark:border-dark-border rounded-lg overflow-hidden">
          <button
            onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors cursor-pointer"
          >
            <div className="flex-1 min-w-0 mr-4">
              <p className="text-sm font-medium text-text dark:text-dark-text truncate">{q.question}</p>
              <div className="flex gap-4 mt-1">
                {metricKeys.slice(0, 3).map((key) => (
                  <span key={key} className="text-xs text-text-muted dark:text-dark-text-muted">
                    {key.split('_').map(w => w[0].toUpperCase()).join('')}:{' '}
                    <span className="font-mono">{q[key] != null ? (q[key] as number).toFixed(3) : '—'}</span>
                  </span>
                ))}
              </div>
            </div>
            {expandedIndex === i ? (
              <ChevronUp className="h-4 w-4 text-text-muted flex-shrink-0" />
            ) : (
              <ChevronDown className="h-4 w-4 text-text-muted flex-shrink-0" />
            )}
          </button>
          {expandedIndex === i && (
            <div className="px-4 pb-4 border-t border-border dark:border-dark-border pt-3">
              <div className="grid grid-cols-4 gap-3">
                {metricKeys.map((key) => (
                  <div key={key} className="text-center p-2 rounded-lg bg-surface dark:bg-dark-surface-alt">
                    <p className="text-xs text-text-muted dark:text-dark-text-muted capitalize">
                      {key.replace('_', ' ')}
                    </p>
                    <p className="text-lg font-bold text-text dark:text-dark-text">
                      {q[key] != null ? (q[key] as number).toFixed(3) : '—'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
