import { useState, useEffect } from 'react';
import { Play } from 'lucide-react';
import PageLayout from '../components/layout/PageLayout';
import ScoreCards from '../components/eval/ScoreCards';
import ScoreChart from '../components/eval/ScoreChart';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import { getEvalResults } from '../api/eval';
import type { EvalResults } from '../types/eval';
import toast from 'react-hot-toast';

export default function EvalPage() {
  const [results, setResults] = useState<EvalResults | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    try {
      const data = await getEvalResults();
      setResults(data);
    } catch {
      // No results yet — that's fine
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  if (loading) return <PageLayout title="Evaluation"><LoadingSpinner fullPage label="Loading evaluation results..." /></PageLayout>;

  const latestRun = results?.results?.[0] ?? null;

  return (
    <PageLayout title="Evaluation Dashboard">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted dark:text-dark-text-muted">
            RAGAS evaluation metrics across the 50-question test set.
          </p>
          <Button variant="secondary" onClick={fetchResults} loading={loading}>
            Refresh
          </Button>
        </div>

        {/* Score Cards (latest run) */}
        <ScoreCards metrics={latestRun} />

        {/* Score History Chart */}
        <Card title="Score History">
          <ScoreChart history={results?.results ?? []} />
        </Card>
      </div>
    </PageLayout>
  );
}
