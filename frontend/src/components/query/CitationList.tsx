import type { Citation } from '../../types/query';
import CitationCard from './CitationCard';

interface CitationListProps {
  citations: Citation[];
}

export default function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-text dark:text-dark-text">
        Sources ({citations.length})
      </h3>
      <div className="space-y-2">
        {citations.map((c) => (
          <CitationCard key={c.source_number} citation={c} />
        ))}
      </div>
    </div>
  );
}
