import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import { setApiKeyGetter } from '../api/client';

interface AuthState {
  tenantId: string | null;
  tenantName: string | null;
  apiKey: string | null;
}

type AuthAction =
  | { type: 'SET_TENANT'; tenantId: string; tenantName: string; apiKey: string }
  | { type: 'CLEAR_TENANT' };

interface AuthContextValue extends AuthState {
  setTenant: (tenantId: string, tenantName: string, apiKey: string) => void;
  clearTenant: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = 'rag_auth';

function loadInitialState(): AuthState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch { /* ignore */ }
  return { tenantId: null, tenantName: null, apiKey: null };
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_TENANT':
      return { tenantId: action.tenantId, tenantName: action.tenantName, apiKey: action.apiKey };
    case 'CLEAR_TENANT':
      return { tenantId: null, tenantName: null, apiKey: null };
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

  const setTenant = (tenantId: string, tenantName: string, apiKey: string) => {
    dispatch({ type: 'SET_TENANT', tenantId, tenantName, apiKey });
  };

  const clearTenant = () => {
    dispatch({ type: 'CLEAR_TENANT' });
  };

  return (
    <AuthContext.Provider value={{ ...state, setTenant, clearTenant }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
