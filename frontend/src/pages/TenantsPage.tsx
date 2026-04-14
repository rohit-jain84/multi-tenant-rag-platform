import { useState } from 'react';
import { Plus } from 'lucide-react';
import PageLayout from '../components/layout/PageLayout';
import TenantList from '../components/tenants/TenantList';
import CreateTenantForm from '../components/tenants/CreateTenantForm';
import UsageStats from '../components/tenants/UsageStats';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import { useTenants } from '../hooks/useTenants';
import { getTenantUsage } from '../api/tenants';
import { useAuth } from '../context/AuthContext';
import type { Tenant, TenantUsage } from '../types/tenant';

export default function TenantsPage() {
  const { tenants, loading, refresh } = useTenants();
  const { setTenant } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [usage, setUsage] = useState<TenantUsage | null>(null);
  const [loadingUsage, setLoadingUsage] = useState(false);

  const handleSelectTenant = async (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setLoadingUsage(true);
    try {
      const data = await getTenantUsage(tenant.id);
      setUsage(data);
    } catch {
      setUsage(null);
    } finally {
      setLoadingUsage(false);
    }
  };

  return (
    <PageLayout title="Tenant Management">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted dark:text-dark-text-muted">
            Manage tenants, API keys, and view usage statistics.
          </p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4" />
            New Tenant
          </Button>
        </div>

        {/* Tenant List */}
        <Card title="Tenants">
          {loading ? (
            <LoadingSpinner label="Loading tenants..." />
          ) : (
            <TenantList tenants={tenants} onSelectTenant={handleSelectTenant} loading={loading} />
          )}
        </Card>

        {/* Usage Stats */}
        {selectedTenant && (
          <Card title={`Usage — ${selectedTenant.name}`}>
            {loadingUsage ? <LoadingSpinner label="Loading usage..." /> : <UsageStats usage={usage} />}
          </Card>
        )}

        {/* Create Modal */}
        <CreateTenantForm open={showCreate} onClose={() => setShowCreate(false)} onCreated={refresh} />
      </div>
    </PageLayout>
  );
}
