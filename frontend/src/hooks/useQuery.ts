import { useCallback } from 'react';
import { useSSE } from './useSSE';
import { useAuth } from '../context/AuthContext';
import type { QueryRequest } from '../types/query';

export function useQuery() {
  const { apiKey } = useAuth();
  const sse = useSSE();

  const submitQuery = useCallback(
    (request: QueryRequest) => {
      sse.stream(request, apiKey);
    },
    [apiKey, sse.stream],
  );

  return {
    answer: sse.answer,
    citations: sse.citations,
    latency: sse.latency,
    isStreaming: sse.isStreaming,
    error: sse.error,
    submitQuery,
    cancel: sse.cancel,
  };
}
