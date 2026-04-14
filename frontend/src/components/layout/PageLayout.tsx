import type { ReactNode } from 'react';
import Header from './Header';
import ErrorBoundary from '../shared/ErrorBoundary';

interface PageLayoutProps {
  title: string;
  children: ReactNode;
}

export default function PageLayout({ title, children }: PageLayoutProps) {
  return (
    <div className="flex-1 flex flex-col min-h-screen">
      <Header title={title} />
      <main className="flex-1 p-6 bg-surface/50 dark:bg-dark-bg overflow-auto">
        <div className="max-w-6xl mx-auto">
          <ErrorBoundary>{children}</ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
