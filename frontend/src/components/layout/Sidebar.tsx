import { NavLink } from 'react-router-dom';
import { FileText, MessageSquare, BarChart3, Users, Activity, ChevronLeft, ChevronRight, Sun, Moon } from 'lucide-react';
import { useState } from 'react';
import { ROUTES } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';

const navItems = [
  { path: ROUTES.DOCUMENTS, label: 'Documents', icon: FileText },
  { path: ROUTES.QUERY, label: 'Query', icon: MessageSquare },
  { path: ROUTES.EVAL, label: 'Evaluation', icon: BarChart3 },
  { path: ROUTES.TENANTS, label: 'Tenants', icon: Users },
  { path: ROUTES.HEALTH, label: 'Health', icon: Activity },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { isDark, toggle: toggleTheme } = useTheme();

  return (
    <aside
      className={`flex flex-col bg-white dark:bg-dark-surface border-r border-border dark:border-dark-border
        transition-all duration-200 ${collapsed ? 'w-16' : 'w-56'} min-h-screen`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-border dark:border-dark-border">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-sm">R</span>
        </div>
        {!collapsed && (
          <span className="font-semibold text-sm text-text dark:text-dark-text truncate">
            RAG Platform
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
              ${isActive
                ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-blue-300'
                : 'text-text-muted dark:text-dark-text-muted hover:bg-surface dark:hover:bg-dark-surface-alt'
              }`
            }
          >
            <Icon className="h-5 w-5 flex-shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Theme Toggle + Collapse */}
      <div className="border-t border-border dark:border-dark-border">
        <button
          onClick={toggleTheme}
          className="flex items-center gap-3 w-full px-3 py-2.5 text-text-muted dark:text-dark-text-muted
            hover:bg-surface dark:hover:bg-dark-surface-alt transition-colors cursor-pointer"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <Sun className="h-5 w-5 flex-shrink-0" /> : <Moon className="h-5 w-5 flex-shrink-0" />}
          {!collapsed && <span className="text-sm">{isDark ? 'Light Mode' : 'Dark Mode'}</span>}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full p-3
            text-text-muted dark:text-dark-text-muted hover:bg-surface dark:hover:bg-dark-surface-alt
            transition-colors cursor-pointer"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  );
}
