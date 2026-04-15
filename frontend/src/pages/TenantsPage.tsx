import { useState } from 'react';
import { Plus, KeyRound, LogOut, ShieldCheck } from 'lucide-react';
import PageLayout from '../components/layout/PageLayout';
import TenantList from '../components/tenants/TenantList';
import CreateTenantForm from '../components/tenants/CreateTenantForm';
import UsageStats from '../components/tenants/UsageStats';
import ApiKeyPrompt from '../components/tenants/ApiKeyPrompt';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import { useTenants } from '../hooks/useTenants';
import { getTenantUsage } from '../api/tenants';
import { useAuth } from '../context/AuthContext';
import type { Tenant, TenantUsage } from '../types/tenant';

export default function TenantsPage() {
  const { tenants, loading, refresh } = useTenants();
  const { setTenant, adminApiKey, setAdminKey, clearAdminKey } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [usage, setUsage] = useState<TenantUsage | null>(null);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [showAdminInput, setShowAdminInput] = useState(false);
  const [adminKeyInput, setAdminKeyInput] = useState('');
  const [connectTenant, setConnectTenant] = useState<Tenant | null>(null);

  const handleSelectTenant = async (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setConnectTenant(tenant);
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

  const handleAdminKeySubmit = () => {
    if (!adminKeyInput.trim()) return;
    setAdminKey(adminKeyInput.trim());
    setAdminKeyInput('');
    setShowAdminInput(false);
    refresh();
  };

  const handleTenantCreated = (tenantId: string, tenantName: string, apiKey: string) => {
    setTenant(tenantId, tenantName, apiKey);
    refresh();
  };

  const handleConnectTenant = (apiKey: string) => {
    if (!connectTenant) return;
    setTenant(connectTenant.id, connectTenant.name, apiKey);
    setConnectTenant(null);
  };

  return (
    <PageLayout title="Tenant Management">
      <div className="space-y-6">
        {/* Admin Key Banner */}
        {!adminApiKey ? (
          <div className="flex items-center gap-4 p-4 rounded-xl border border-warning/30 bg-warning/5">
            <KeyRound className="h-5 w-5 text-warning flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-text dark:text-dark-text">Admin API key required</p>
              <p className="text-xs text-text-muted dark:text-dark-text-muted mt-0.5">
                Enter your admin API key to manage tenants and access admin endpoints.
              </p>
            </div>
            {showAdminInput ? (
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={adminKeyInput}
                  onChange={(e) => setAdminKeyInput(e.target.value)}
                  placeholder="Admin API key"
                  autoFocus
                  className="px-3 py-1.5 text-sm rounded-lg border border-border dark:border-dark-border
                    bg-white dark:bg-dark-surface text-text dark:text-dark-text
                    focus:outline-none focus:ring-2 focus:ring-primary/30 w-64"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleAdminKeySubmit();
                    if (e.key === 'Escape') setShowAdminInput(false);
                  }}
                />
                <Button size="sm" onClick={handleAdminKeySubmit} disabled={!adminKeyInput.trim()}>
                  Connect
                </Button>
              </div>
            ) : (
              <Button size="sm" onClick={() => setShowAdminInput(true)}>
                <KeyRound className="h-3.5 w-3.5" />
                Set Key
              </Button>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl border border-success/30 bg-success/5">
            <ShieldCheck className="h-4 w-4 text-success flex-shrink-0" />
            <span className="text-xs font-medium text-success">Admin connected</span>
            <span className="text-xs text-text-muted dark:text-dark-text-muted font-mono">
              ...{adminApiKey.slice(-6)}
            </span>
            <button
              onClick={clearAdminKey}
              className="ml-auto text-text-muted hover:text-danger transition-colors cursor-pointer"
              title="Disconnect admin key"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted dark:text-dark-text-muted">
            Manage tenants, API keys, and view usage statistics.
          </p>
          <Button onClick={() => setShowCreate(true)} disabled={!adminApiKey}>
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
        <CreateTenantForm
          open={showCreate}
          onClose={() => setShowCreate(false)}
          onCreated={handleTenantCreated}
        />

        {/* Connect Tenant Modal (enter API key for existing tenant) */}
        <ApiKeyPrompt
          open={!!connectTenant}
          tenantName={connectTenant?.name || ''}
          onClose={() => setConnectTenant(null)}
          onSubmit={handleConnectTenant}
        />
      </div>
    </PageLayout>
  );
}
