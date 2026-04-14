import type { TenantUsage } from '../../types/tenant';
import { formatTokens, formatCost } from '../../utils/formatters';
import Card from '../shared/Card';

interface UsageStatsProps {
  usage: TenantUsage | null;
}

export default function UsageStats({ usage }: UsageStatsProps) {
  if (!usage) {
    return (
      <p className="text-sm text-text-muted dark:text-dark-text-muted py-4 text-center">
        Select a tenant to view usage statistics.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-xs font-medium text-text-muted dark:text-dark-text-muted uppercase tracking-wider mb-1">Total Queries</p>
          <p className="text-2xl font-bold text-text dark:text-dark-text">{usage.total_queries.toLocaleString()}</p>
        </Card>
        <Card>
          <p className="text-xs font-medium text-text-muted dark:text-dark-text-muted uppercase tracking-wider mb-1">Total Tokens</p>
          <p className="text-2xl font-bold text-text dark:text-dark-text">{formatTokens(usage.total_tokens)}</p>
        </Card>
        <Card>
          <p className="text-xs font-medium text-text-muted dark:text-dark-text-muted uppercase tracking-wider mb-1">Estimated Cost</p>
          <p className="text-2xl font-bold text-text dark:text-dark-text">{formatCost(usage.total_estimated_cost)}</p>
        </Card>
        <Card>
          <p className="text-xs font-medium text-text-muted dark:text-dark-text-muted uppercase tracking-wider mb-1">Documents</p>
          <p className="text-2xl font-bold text-text dark:text-dark-text">{usage.document_count}</p>
        </Card>
      </div>
    </div>
  );
}
