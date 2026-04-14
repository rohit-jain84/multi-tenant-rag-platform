import { useState, useEffect, useCallback } from 'react';
import { listDocuments, getDocument } from '../api/documents';
import type { Document } from '../types/document';
import { DEFAULTS } from '../utils/constants';

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listDocuments(page, DEFAULTS.PAGE_SIZE);
      setDocuments(result.documents);
      setTotal(result.total);
    } catch (err) {
      setError((err as Error).message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Poll for processing documents
  useEffect(() => {
    const processing = documents.filter((d) => d.status === 'processing' || d.status === 'queued');
    if (processing.length === 0) return;

    const interval = setInterval(async () => {
      const updates = await Promise.allSettled(processing.map((d) => getDocument(d.id)));
      setDocuments((prev) =>
        prev.map((doc) => {
          const updated = updates.find(
            (u) => u.status === 'fulfilled' && u.value.id === doc.id,
          );
          return updated && updated.status === 'fulfilled' ? updated.value : doc;
        }),
      );
    }, DEFAULTS.STATUS_POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [documents]);

  return { documents, total, page, setPage, loading, error, refresh: fetchDocuments };
}
