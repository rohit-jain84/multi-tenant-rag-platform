import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { EvalRun } from '../../types/eval';
import { formatDate } from '../../utils/formatters';

interface ScoreChartProps {
  history: EvalRun[];
}

export default function ScoreChart({ history }: ScoreChartProps) {
  const data = history.map((run) => ({
    date: formatDate(run.created_at),
    'Context Recall': run.context_recall,
    'Faithfulness': run.faithfulness,
    'Answer Relevancy': run.answer_relevancy,
    'Context Precision': run.context_precision,
  }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-text-muted dark:text-dark-text-muted">
        No evaluation history available yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e4e8" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
        <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} stroke="#6b7280" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e2e4e8',
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="Context Recall" stroke="#e94560" strokeWidth={2} dot={{ r: 4 }} />
        <Line type="monotone" dataKey="Faithfulness" stroke="#0f3460" strokeWidth={2} dot={{ r: 4 }} />
        <Line type="monotone" dataKey="Answer Relevancy" stroke="#3498db" strokeWidth={2} dot={{ r: 4 }} />
        <Line type="monotone" dataKey="Context Precision" stroke="#2ecc71" strokeWidth={2} dot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
