import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/layout/Sidebar';
import DocumentsPage from './pages/DocumentsPage';
import QueryPage from './pages/QueryPage';
import EvalPage from './pages/EvalPage';
import TenantsPage from './pages/TenantsPage';
import HealthPage from './pages/HealthPage';
import { ROUTES } from './utils/constants';

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <div className="flex min-h-screen bg-white dark:bg-dark-bg">
            <Sidebar />
            <div className="flex-1 min-w-0">
              <Routes>
                <Route path={ROUTES.DOCUMENTS} element={<DocumentsPage />} />
                <Route path={ROUTES.QUERY} element={<QueryPage />} />
                <Route path={ROUTES.EVAL} element={<EvalPage />} />
                <Route path={ROUTES.TENANTS} element={<TenantsPage />} />
                <Route path={ROUTES.HEALTH} element={<HealthPage />} />
                <Route path="*" element={<Navigate to={ROUTES.QUERY} replace />} />
              </Routes>
            </div>
          </div>
          <Toaster
            position="bottom-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#fff',
                color: '#1a1a2e',
                border: '1px solid #e2e4e8',
                borderRadius: '10px',
                fontSize: '14px',
              },
            }}
          />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
