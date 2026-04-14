import { useState, useEffect, useCallback } from 'react';
import { listTenants } from '../api/tenants';
import type { Tenant } from '../types/tenant';

export function useTenants() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTenants = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listTenants();
      setTenants(data);
    } catch (err) {
      setError((err as Error).message || 'Failed to load tenants');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTenants();
  }, [fetchTenants]);

  return { tenants, loading, error, refresh: fetchTenants };
}
