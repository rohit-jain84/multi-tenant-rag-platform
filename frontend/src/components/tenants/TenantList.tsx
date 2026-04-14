import { Users } from 'lucide-react';
import EmptyState from '../shared/EmptyState';
import { formatDate } from '../../utils/formatters';
import type { Tenant } from '../../types/tenant';

interface TenantListProps {
  tenants: Tenant[];
  onSelectTenant: (tenant: Tenant) => void;
  loading: boolean;
}

export default function TenantList({ tenants, onSelectTenant, loading }: TenantListProps) {
  if (!loading && tenants.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title="No tenants yet"
        description="Create your first tenant to start using the platform."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border dark:border-dark-border">
            <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Name</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Created</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Rate Limit (QPM)</th>
            <th className="text-center py-3 px-4 text-xs font-semibold text-text-muted dark:text-dark-text-muted uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border dark:divide-dark-border">
          {tenants.map((tenant) => (
            <tr
              key={tenant.id}
              onClick={() => onSelectTenant(tenant)}
              className="hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors cursor-pointer"
            >
              <td className="py-3 px-4">
                <span className="text-sm font-medium text-text dark:text-dark-text">{tenant.name}</span>
              </td>
              <td className="py-3 px-4 text-sm text-text-muted dark:text-dark-text-muted">
                {formatDate(tenant.created_at)}
              </td>
              <td className="py-3 px-4 text-sm text-right font-mono text-text-muted dark:text-dark-text-muted">
                {tenant.rate_limit_qpm}
              </td>
              <td className="py-3 px-4 text-sm text-center">
                <span className={`inline-block w-2 h-2 rounded-full ${tenant.is_active ? 'bg-success' : 'bg-danger'}`} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
