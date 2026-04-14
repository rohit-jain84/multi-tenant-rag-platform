import apiClient from './client';
import type { QueryRequest, QueryResponse } from '../types/query';

export async function submitQuery(req: QueryRequest): Promise<QueryResponse> {
  const { data } = await apiClient.post<QueryResponse>('/api/v1/query', req);
  return data;
}

// SSE streaming is handled directly in hooks/useSSE.ts using fetch + ReadableStream

export async function getChunkingStrategies(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/api/v1/admin/config/chunking-strategies');
  return data;
}
