import { useState, useEffect } from 'react';
import { Database, HardDrive, Wifi, RefreshCw } from 'lucide-react';
import PageLayout from '../components/layout/PageLayout';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';
import { getHealth, type HealthStatus } from '../api/health';
import { DEFAULTS } from '../utils/constants';
import { formatMs } from '../utils/formatters';

const serviceConfig = [
  { key: 'postgresql' as const, label: 'PostgreSQL', icon: Database, description: 'Relational store & metadata' },
  { key: 'vector_db' as const, label: 'Vector Database', icon: HardDrive, description: 'Qdrant / pgvector' },
  { key: 'redis' as const, label: 'Redis', icon: Wifi, description: 'Cache & rate limiting' },
];

export default function HealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const data = await getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setLoading(false);
      setLastChecked(new Date());
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, DEFAULTS.HEALTH_POLL_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  return (
    <PageLayout title="System Health">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-text-muted dark:text-dark-text-muted">
              Service connectivity status. Auto-refreshes every 30 seconds.
            </p>
            {lastChecked && (
              <p className="text-xs text-text-muted/70 dark:text-dark-text-muted/70 mt-1">
                Last checked: {lastChecked.toLocaleTimeString()}
              </p>
            )}
          </div>
          <Button variant="secondary" onClick={fetchHealth} loading={loading}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Overall Status */}
        <div className={`p-4 rounded-xl border-2 text-center ${
          health?.status === 'healthy'
            ? 'border-success/30 bg-success/5'
            : health === null
            ? 'border-border bg-surface dark:bg-dark-surface'
            : 'border-danger/30 bg-danger/5'
        }`}>
          <p className="text-lg font-bold">
            {health?.status === 'healthy' ? 'All Systems Operational' :
             health === null ? 'Unable to reach backend' : 'Service Degraded'}
          </p>
        </div>

        {/* Service Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {serviceConfig.map(({ key, label, icon: Icon, description }) => {
            const service = health?.services[key];
            const isUp = service?.status === 'up';
            return (
              <Card key={key}>
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isUp ? 'bg-success/10' : service ? 'bg-danger/10' : 'bg-surface dark:bg-dark-surface-alt'
                  }`}>
                    <Icon className={`h-5 w-5 ${isUp ? 'text-success' : service ? 'text-danger' : 'text-text-muted'}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-text dark:text-dark-text">{label}</p>
                      <div className={`w-2.5 h-2.5 rounded-full ${isUp ? 'bg-success' : service ? 'bg-danger' : 'bg-border'}`} />
                    </div>
                    <p className="text-xs text-text-muted dark:text-dark-text-muted mt-0.5">{description}</p>
                    {service?.latency_ms != null && (
                      <p className="text-xs font-mono text-text-muted dark:text-dark-text-muted mt-1">
                        Latency: {formatMs(service.latency_ms)}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </PageLayout>
  );
}
