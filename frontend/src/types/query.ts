import type { ChunkingStrategy } from '../utils/constants';

export interface Citation {
  source_number: number;
  document_name: string;
  document_id: string;
  page_number?: number;
  section_heading?: string;
  chunk_text: string;
  relevance_score: number;
}

export interface LatencyBreakdown {
  embedding_and_dense_ms: number;
  sparse_ms: number;
  fusion_ms: number;
  retrieval_ms: number;
  reranking_ms: number;
  generation_ms: number;
  total_ms: number;
}

export interface QueryRequest {
  question: string;
  top_k?: number;
  top_n?: number;
  search_type?: 'hybrid' | 'dense_only';
  chunking_strategy?: ChunkingStrategy;
  filters?: {
    document_ids?: string[];
    categories?: string[];
    date_range?: { start: string; end: string };
  };
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  query_metadata: {
    latency: LatencyBreakdown;
    tokens: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    retrieval_strategy: string;
    reranking_enabled: boolean;
    chunks_retrieved: number;
  };
}
