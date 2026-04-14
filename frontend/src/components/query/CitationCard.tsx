import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
import type { Citation } from '../../types/query';
import { truncateText } from '../../utils/formatters';

interface CitationCardProps {
  citation: Citation;
}

export default function CitationCard({ citation }: CitationCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      id={`citation-${citation.source_number}`}
      className="border border-border dark:border-dark-border rounded-lg overflow-hidden bg-white dark:bg-dark-surface"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <span className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">
            {citation.source_number}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 text-text-muted dark:text-dark-text-muted flex-shrink-0" />
              <span className="text-sm font-medium text-text dark:text-dark-text truncate">
                {citation.document_name}
              </span>
              {citation.page_number && (
                <span className="text-xs text-text-muted dark:text-dark-text-muted">
                  p.{citation.page_number}
                </span>
              )}
            </div>
            {!expanded && (
              <p className="text-xs text-text-muted dark:text-dark-text-muted mt-0.5 truncate">
                {truncateText(citation.chunk_text, 120)}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-3">
          <span className="text-xs font-mono text-text-muted dark:text-dark-text-muted">
            {(citation.relevance_score * 100).toFixed(1)}%
          </span>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-text-muted" />
          ) : (
            <ChevronDown className="h-4 w-4 text-text-muted" />
          )}
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-border dark:border-dark-border">
          <p className="text-sm text-text-muted dark:text-dark-text-muted leading-relaxed whitespace-pre-wrap">
            {citation.chunk_text}
          </p>
        </div>
      )}
    </div>
  );
}
