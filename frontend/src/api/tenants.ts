import apiClient from './client';
import type { Tenant, TenantUsage, CreateTenantRequest, CreateTenantResponse } from '../types/tenant';

export async function createTenant(req: CreateTenantRequest): Promise<CreateTenantResponse> {
  const { data } = await apiClient.post<CreateTenantResponse>('/api/v1/admin/tenants', req);
  return data;
}

export async function getTenantUsage(tenantId: string): Promise<TenantUsage> {
  const { data } = await apiClient.get<TenantUsage>(`/api/v1/admin/tenants/${tenantId}/usage`);
  return data;
}

export async function listTenants(): Promise<Tenant[]> {
  const { data } = await apiClient.get<Tenant[]>('/api/v1/admin/tenants');
  return data;
}
