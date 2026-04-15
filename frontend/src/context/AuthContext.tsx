import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
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

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  useEffect(() => {
    setApiKeyGetter(() => state.apiKey);
  }, [state.apiKey]);

  useEffect(() => {
    setAdminApiKeyGetter(() => state.adminApiKey);
  }, [state.adminApiKey]);

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
