import { useState } from 'react';
import { Send, Settings2, X } from 'lucide-react';
import Button from '../shared/Button';
import { CHUNKING_STRATEGIES, DEFAULTS, type ChunkingStrategy } from '../../utils/constants';
import type { QueryRequest } from '../../types/query';

interface QueryInputProps {
  onSubmit: (request: QueryRequest) => void;
  onCancel: () => void;
  isStreaming: boolean;
}

export default function QueryInput({ onSubmit, onCancel, isStreaming }: QueryInputProps) {
  const [question, setQuestion] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [topK, setTopK] = useState<number>(DEFAULTS.TOP_K);
  const [topN, setTopN] = useState<number>(DEFAULTS.TOP_N);
  const [strategy, setStrategy] = useState<ChunkingStrategy>('fixed');
  const [category, setCategory] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isStreaming) return;
    onSubmit({
      question: question.trim(),
      top_k: topK,
      top_n: topN,
      search_type: 'hybrid',
      chunking_strategy: strategy,
      filters: category ? { categories: [category] } : undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents..."
          rows={3}
          className="w-full px-4 py-3 pr-24 text-sm rounded-xl border border-border dark:border-dark-border
            bg-white dark:bg-dark-surface text-text dark:text-dark-text
            focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <div className="absolute right-2 bottom-2 flex items-center gap-1">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`p-2 rounded-lg transition-colors cursor-pointer
              ${showAdvanced ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-surface dark:hover:bg-dark-surface-alt'}`}
            title="Advanced options"
          >
            <Settings2 className="h-4 w-4" />
          </button>
          {isStreaming ? (
            <Button type="button" variant="danger" size="sm" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="submit" size="sm" disabled={!question.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border">
          <div>
            <label className="block text-xs font-medium text-text-muted dark:text-dark-text-muted mb-1">
              Top K (candidates)
            </label>
            <input
              type="number"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              min={1}
              max={100}
              className="w-full px-3 py-1.5 text-sm rounded-lg border border-border dark:border-dark-border
                bg-surface dark:bg-dark-surface-alt text-text dark:text-dark-text
                focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-muted dark:text-dark-text-muted mb-1">
              Top N (final)
            </label>
            <input
              type="number"
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              min={1}
              max={20}
              className="w-full px-3 py-1.5 text-sm rounded-lg border border-border dark:border-dark-border
                bg-surface dark:bg-dark-surface-alt text-text dark:text-dark-text
                focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-muted dark:text-dark-text-muted mb-1">
              Chunking Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as ChunkingStrategy)}
              className="w-full px-3 py-1.5 text-sm rounded-lg border border-border dark:border-dark-border
                bg-surface dark:bg-dark-surface-alt text-text dark:text-dark-text
                focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              {CHUNKING_STRATEGIES.map((s) => (
                <option key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-text-muted dark:text-dark-text-muted mb-1">
              Category Filter
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="All categories"
              className="w-full px-3 py-1.5 text-sm rounded-lg border border-border dark:border-dark-border
                bg-surface dark:bg-dark-surface-alt text-text dark:text-dark-text
                focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>
      )}
    </form>
  );
}
