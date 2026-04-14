import apiClient from './client';

export interface ServiceStatus {
  status: 'up' | 'down';
  latency_ms?: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  services: {
    postgresql: ServiceStatus;
    vector_db: ServiceStatus;
    redis: ServiceStatus;
  };
}

export async function getHealth(): Promise<HealthStatus> {
  const { data } = await apiClient.get<HealthStatus>('/health');
  return data;
}
