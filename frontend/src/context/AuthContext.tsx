import { createContext, useContext, useReducer, useEffect, useRef, type ReactNode } from 'react';
import { setApiKeyGetter, setAdminApiKeyGetter } from '../api/client';

interface AuthState {
  tenantId: string | null;
  tenantName: string | null;
  apiKey: string | null;
  adminApiKey: string | null;
}

type AuthAction =
  | { type: 'SET_TENANT'; tenantId: string; tenantName: string; apiKey: string }
  | { type: 'CLEAR_TENANT' }
  | { type: 'SET_ADMIN_KEY'; adminApiKey: string }
  | { type: 'CLEAR_ADMIN_KEY' };

interface AuthContextValue extends AuthState {
  setTenant: (tenantId: string, tenantName: string, apiKey: string) => void;
  clearTenant: () => void;
  setAdminKey: (key: string) => void;
  clearAdminKey: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = 'rag_auth';

function loadInitialState(): AuthState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return { tenantId: null, tenantName: null, apiKey: null, adminApiKey: null, ...JSON.parse(stored) };
  } catch { /* ignore */ }
  return { tenantId: null, tenantName: null, apiKey: null, adminApiKey: null };
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_TENANT':
      return { ...state, tenantId: action.tenantId, tenantName: action.tenantName, apiKey: action.apiKey };
    case 'CLEAR_TENANT':
      return { ...state, tenantId: null, tenantName: null, apiKey: null };
    case 'SET_ADMIN_KEY':
      return { ...state, adminApiKey: action.adminApiKey };
    case 'CLEAR_ADMIN_KEY':
      return { ...state, adminApiKey: null };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, undefined, loadInitialState);

  // Use refs so the getter closures always return the latest value.
  // This avoids the race condition where child effects (e.g. useTenants)
  // fire before parent effects, meaning the getter would still be null
  // when the first API call is made.
  const apiKeyRef = useRef(state.apiKey);
  const adminApiKeyRef = useRef(state.adminApiKey);

  // Keep refs in sync on every render (synchronous, no effect delay).
  apiKeyRef.current = state.apiKey;
  adminApiKeyRef.current = state.adminApiKey;

  // Register the getter functions once — they read from refs so they
  // always return the current value without needing to be re-registered.
  useEffect(() => {
    setApiKeyGetter(() => apiKeyRef.current);
    setAdminApiKeyGetter(() => adminApiKeyRef.current);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const setTenant = (tenantId: string, tenantName: string, apiKey: string) => {
    dispatch({ type: 'SET_TENANT', tenantId, tenantName, apiKey });
  };

  const clearTenant = () => {
    dispatch({ type: 'CLEAR_TENANT' });
  };

  const setAdminKey = (key: string) => {
    dispatch({ type: 'SET_ADMIN_KEY', adminApiKey: key });
  };

  const clearAdminKey = () => {
    dispatch({ type: 'CLEAR_ADMIN_KEY' });
  };

  return (
    <AuthContext.Provider value={{ ...state, setTenant, clearTenant, setAdminKey, clearAdminKey }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
