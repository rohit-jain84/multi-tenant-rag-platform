import { useState, useRef, useCallback } from 'react';
import type { Citation, LatencyBreakdown } from '../types/query';
import type { QueryRequest } from '../types/query';

interface SSEState {
  answer: string;
  citations: Citation[];
  latency: LatencyBreakdown | null;
  isStreaming: boolean;
  error: string | null;
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    answer: '',
    citations: [],
    latency: null,
    isStreaming: false,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(async (request: QueryRequest, apiKey: string | null) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ answer: '', citations: [], latency: null, isStreaming: true, error: null });

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

      const response = await fetch(`${baseUrl}/api/v1/query/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.error?.message || `HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No readable stream');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              setState((prev) => ({ ...prev, isStreaming: false }));
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'token') {
                setState((prev) => ({ ...prev, answer: prev.answer + parsed.content }));
              } else if (parsed.type === 'citations') {
                setState((prev) => ({ ...prev, citations: parsed.content }));
              } else if (parsed.type === 'metadata') {
                setState((prev) => ({ ...prev, latency: parsed.content?.latency ?? null }));
              } else if (parsed.type === 'done') {
                setState((prev) => ({ ...prev, isStreaming: false }));
                return;
              }
            } catch {
              // Plain text token
              setState((prev) => ({ ...prev, answer: prev.answer + data }));
            }
          }
        }
      }

      setState((prev) => ({ ...prev, isStreaming: false }));
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;
      setState((prev) => ({
        ...prev,
        isStreaming: false,
        error: (err as Error).message || 'Streaming failed',
      }));
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  return { ...state, stream, cancel };
}
