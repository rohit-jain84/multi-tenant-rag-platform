import PageLayout from '../components/layout/PageLayout';
import QueryInput from '../components/query/QueryInput';
import AnswerDisplay from '../components/query/AnswerDisplay';
import CitationList from '../components/query/CitationList';
import LatencyBreakdown from '../components/query/LatencyBreakdown';
import Card from '../components/shared/Card';
import { useQuery } from '../hooks/useQuery';

export default function QueryPage() {
  const { answer, citations, latency, isStreaming, error, submitQuery, cancel } = useQuery();

  return (
    <PageLayout title="Query Playground">
      <div className="space-y-6">
        {/* Input */}
        <QueryInput onSubmit={submitQuery} onCancel={cancel} isStreaming={isStreaming} />

        {/* Answer */}
        <AnswerDisplay answer={answer} isStreaming={isStreaming} error={error} />

        {/* Latency */}
        {latency && (
          <Card>
            <LatencyBreakdown latency={latency} />
          </Card>
        )}

        {/* Citations */}
        <CitationList citations={citations} />
      </div>
    </PageLayout>
  );
}
