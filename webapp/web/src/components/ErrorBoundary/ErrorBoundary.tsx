import React, { Component, ErrorInfo, ReactNode } from 'react';
import './ErrorBoundary.css';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Log to error reporting service
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // In production, send error to monitoring service
    if (process.env.NODE_ENV === 'production') {
      // Example: Sentry, LogRocket, etc.
      console.log('Sending error to monitoring service:', {
        error: error.toString(),
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
      });
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      return (
        <div className="error-boundary-container">
          <div className="error-boundary-content">
            <div className="error-boundary-icon">⚠️</div>
            <h1 className="error-boundary-title">Something went wrong</h1>
            <p className="error-boundary-message">
              An unexpected error occurred. The application encountered a problem and couldn't recover.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-boundary-details">
                <summary>Error Details (Development Only)</summary>
                <div className="error-details-content">
                  <h3>Error Message:</h3>
                  <pre>{this.state.error.toString()}</pre>

                  {this.state.error.stack && (
                    <>
                      <h3>Stack Trace:</h3>
                      <pre>{this.state.error.stack}</pre>
                    </>
                  )}

                  {this.state.errorInfo && (
                    <>
                      <h3>Component Stack:</h3>
                      <pre>{this.state.errorInfo.componentStack}</pre>
                    </>
                  )}
                </div>
              </details>
            )}

            <div className="error-boundary-actions">
              <button
                className="error-boundary-button primary"
                onClick={this.handleReset}
              >
                Try Again
              </button>
              <button
                className="error-boundary-button secondary"
                onClick={() => window.location.href = '/'}
              >
                Go Home
              </button>
            </div>

            {this.state.errorCount > 2 && (
              <div className="error-boundary-warning">
                <p>Multiple errors detected. Try refreshing the page.</p>
                <button
                  className="error-boundary-button tertiary"
                  onClick={() => window.location.reload()}
                >
                  Refresh Page
                </button>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Specific error boundary for async components
export const AsyncErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <ErrorBoundary
      fallback={
        <div className="async-error-container">
          <div className="async-error-content">
            <div className="loading-spinner" />
            <p>Failed to load component. Please try again.</p>
            <button
              className="retry-button"
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
};