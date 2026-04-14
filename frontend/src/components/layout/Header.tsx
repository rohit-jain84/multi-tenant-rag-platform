import { Sun, Moon, Key, LogOut } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  title: string;
}

export default function Header({ title }: HeaderProps) {
  const { isDark, toggle } = useTheme();
  const { tenantName, apiKey, clearTenant } = useAuth();

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border dark:border-dark-border bg-white dark:bg-dark-surface">
      <h1 className="text-xl font-bold text-text dark:text-dark-text">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Tenant Info */}
        {tenantName && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface dark:bg-dark-surface-alt">
            <Key className="h-3.5 w-3.5 text-text-muted dark:text-dark-text-muted" />
            <span className="text-xs font-medium text-text-muted dark:text-dark-text-muted">
              {tenantName}
            </span>
            <span className="text-xs text-text-muted/60 dark:text-dark-text-muted/60 font-mono">
              {apiKey ? `...${apiKey.slice(-6)}` : ''}
            </span>
            <button
              onClick={clearTenant}
              className="ml-1 text-text-muted hover:text-danger transition-colors cursor-pointer"
              title="Switch tenant"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggle}
          className="p-2 rounded-lg text-text-muted dark:text-dark-text-muted
            hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors cursor-pointer"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
      </div>
    </header>
  );
}
