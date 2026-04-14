import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  title?: string;
  className?: string;
  accentColor?: string;
}

export default function Card({ children, title, className = '', accentColor }: CardProps) {
  return (
    <div
      className={`bg-white border border-border rounded-xl p-5 transition-all hover:shadow-sm
        dark:bg-dark-surface dark:border-dark-border ${className}`}
      style={accentColor ? { borderLeftColor: accentColor, borderLeftWidth: 3 } : undefined}
    >
      {title && (
        <h3 className="text-base font-semibold mb-3 text-text dark:text-dark-text">{title}</h3>
      )}
      {children}
    </div>
  );
}
