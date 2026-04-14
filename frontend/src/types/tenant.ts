export interface Tenant {
  id: string;
  name: string;
  is_active: boolean;
  rate_limit_qpm: number;
  created_at: string;
}

export interface TenantUsage {
  tenant_id: string;
  tenant_name: string;
  total_queries: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_estimated_cost: number;
  document_count: number;
}

export interface CreateTenantRequest {
  name: string;
  rate_limit_qpm?: number;
}

export interface CreateTenantResponse {
  tenant: Tenant;
  api_key: string;
}
