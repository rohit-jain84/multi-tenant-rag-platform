import apiClient from './client';
import type { EvalRun, EvalResults } from '../types/eval';

export async function triggerEval(
  tenantId: string,
  strategy: string = 'hybrid',
  rerankingEnabled: boolean = true,
): Promise<EvalRun> {
  const { data } = await apiClient.post<EvalRun>(
    `/api/v1/admin/eval/run?tenant_id=${encodeURIComponent(tenantId)}`,
    { strategy, reranking_enabled: rerankingEnabled },
  );
  return data;
}

export async function getEvalResults(limit: number = 20): Promise<EvalResults> {
  const { data } = await apiClient.get<EvalResults>('/api/v1/admin/eval/results', {
    params: { limit },
  });
  return data;
}
