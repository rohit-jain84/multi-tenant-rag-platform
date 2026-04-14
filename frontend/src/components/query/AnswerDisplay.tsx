import { Loader2 } from 'lucide-react';

interface AnswerDisplayProps {
  answer: string;
  isStreaming: boolean;
  error: string | null;
}

export default function AnswerDisplay({ answer, isStreaming, error }: AnswerDisplayProps) {
  if (error) {
    return (
      <div className="p-4 rounded-xl bg-danger/5 border border-danger/20">
        <p className="text-sm text-danger font-medium">Error: {error}</p>
      </div>
    );
  }

  if (!answer && !isStreaming) return null;

  // Convert [Source N] references to clickable links
  const renderAnswer = (text: string) => {
    const parts = text.split(/(\[Source \d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[Source (\d+)\]$/);
      if (match) {
        const index = match[1];
        return (
          <button
            key={i}
            onClick={() => {
              document.getElementById(`citation-${index}`)?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1 mx-0.5
              text-xs font-bold text-primary bg-primary/10 rounded hover:bg-primary/20
              transition-colors cursor-pointer align-baseline"
          >
            {index}
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="p-5 rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border">
      <div className="prose prose-sm max-w-none text-text dark:text-dark-text leading-relaxed">
        {renderAnswer(answer)}
        {isStreaming && (
          <span className="inline-flex items-center ml-1">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
          </span>
        )}
      </div>
    </div>
  );
}
