import axios from 'axios';
import toast from 'react-hot-toast';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: { 'Content-Type': 'application/json' },
});

// Bootstrap getters from localStorage so admin/tenant keys are available
// immediately — before any React effects fire. The AuthProvider will
// override these with ref-backed getters on mount.
function _bootstrapKey(field: 'apiKey' | 'adminApiKey'): string | null {
  try {
    const stored = localStorage.getItem('rag_auth');
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed[field] ?? null;
    }
  } catch { /* ignore */ }
  return null;
}

let getApiKey: (() => string | null) | null = () => _bootstrapKey('apiKey');
let getAdminApiKey: (() => string | null) | null = () => _bootstrapKey('adminApiKey');

export function setApiKeyGetter(getter: () => string | null) {
  getApiKey = getter;
}

export function setAdminApiKeyGetter(getter: () => string | null) {
  getAdminApiKey = getter;
}

apiClient.interceptors.request.use((config) => {
  const url = config.url || '';
  const isAdmin = url.includes('/admin/');
  const key = isAdmin ? (getAdminApiKey?.() || getApiKey?.()) : getApiKey?.();
  if (key) {
    config.headers.Authorization = `Bearer ${key}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      const message = data?.error?.message || data?.detail || 'An error occurred';

      if (status === 401) {
        toast.error('Invalid or missing API key. Please select a tenant.');
      } else if (status === 429) {
        const retryAfter = error.response.headers['retry-after'];
        toast.error(`Rate limit exceeded. Retry after ${retryAfter || 'a moment'}.`);
      } else if (status >= 500) {
        toast.error(`Server error: ${message}`);
      }
    } else if (error.request) {
      toast.error('Cannot reach the server. Is the backend running?');
    }
    return Promise.reject(error);
  },
);

export default apiClient;
