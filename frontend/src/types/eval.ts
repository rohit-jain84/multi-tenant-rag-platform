export interface EvalRun {
  id: string;
  run_id: string;
  strategy: string;
  reranking_enabled: boolean;
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  context_recall: number | null;
  per_question_results: Record<string, unknown> | null;
  created_at: string;
}

export interface EvalResults {
  results: EvalRun[];
  total: number;
}

export interface ABComparisonResult {
  metric: string;
  hybrid: number;
  dense_only: number;
  improvement: number;
}

export interface RerankComparisonResult {
  metric: string;
  with_reranking: number;
  without_reranking: number;
  improvement: number;
}
