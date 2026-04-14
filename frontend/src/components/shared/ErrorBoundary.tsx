import { Component, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import Button from './Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="h-12 w-12 text-danger mb-4" />
          <h3 className="text-lg font-semibold text-text dark:text-dark-text mb-2">
            Something went wrong
          </h3>
          <p className="text-sm text-text-muted dark:text-dark-text-muted mb-4 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <Button variant="secondary" onClick={() => this.setState({ hasError: false })}>
            Try Again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
