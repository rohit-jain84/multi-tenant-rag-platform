import apiClient from './client';
import type { Document, DocumentListResponse, DocumentUploadRequest } from '../types/document';

export async function uploadDocument(req: DocumentUploadRequest): Promise<Document> {
  const formData = new FormData();
  formData.append('file', req.file);
  if (req.category) formData.append('category', req.category);
  if (req.chunking_strategy) formData.append('chunking_strategy', req.chunking_strategy);

  const { data } = await apiClient.post<Document>('/api/v1/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function listDocuments(page = 1, pageSize = 10): Promise<DocumentListResponse> {
  const { data } = await apiClient.get<DocumentListResponse>('/api/v1/documents', {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getDocument(id: string): Promise<Document> {
  const { data } = await apiClient.get<Document>(`/api/v1/documents/${id}`);
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/documents/${id}`);
}
