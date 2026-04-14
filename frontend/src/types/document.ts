import type { ChunkingStrategy } from '../utils/constants';

export type DocumentStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface Document {
  id: string;
  tenant_id: string;
  filename: string;
  format: string;
  category: string | null;
  status: DocumentStatus;
  error_message?: string | null;
  content_hash?: string | null;
  page_count?: number | null;
  chunk_count?: number | null;
  chunking_strategy?: string | null;
  upload_date: string;
  created_at: string;
}

export interface DocumentUploadRequest {
  file: File;
  category?: string;
  chunking_strategy?: ChunkingStrategy;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}
