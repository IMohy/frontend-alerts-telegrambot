import { Component, type ErrorInfo, type ReactNode } from "react";
import { getJahizTracker, type ReportOptions } from "../jahiz-tracker";

interface Props {
  children: ReactNode;
  /** Component name for error context (e.g. "CheckoutPage") */
  component?: string;
  /** Custom fallback UI when an error is caught */
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  /** Extra options applied to every error captured by this boundary */
  reportOptions?: ReportOptions;
  /** Callback when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary that automatically reports caught errors
 * to the Jahiz webhook and shows a fallback UI.
 *
 * Usage:
 *   <JahizErrorBoundary component="Dashboard" fallback={<ErrorPage />}>
 *     <Dashboard />
 *   </JahizErrorBoundary>
 */
class JahizErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    const tracker = getJahizTracker();
    tracker.captureError(error, {
      severity: "critical",
      component: this.props.component,
      ...this.props.reportOptions,
      metadata: {
        ...this.props.reportOptions?.metadata,
        componentStack: errorInfo.componentStack ?? undefined,
        source: "JahizErrorBoundary",
      },
    });

    this.props.onError?.(error, errorInfo);
  }

  private reset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      if (typeof this.props.fallback === "function") {
        return this.props.fallback(this.state.error, this.reset);
      }

      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback
      return (
        <div
          style={{
            padding: "2rem",
            textAlign: "center",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <h2 style={{ color: "#dc2626" }}>Something went wrong</h2>
          <p style={{ color: "#6b7280" }}>
            The error has been automatically reported.
          </p>
          <button
            onClick={this.reset}
            style={{
              marginTop: "1rem",
              padding: "0.5rem 1.5rem",
              borderRadius: "0.375rem",
              border: "1px solid #d1d5db",
              background: "#fff",
              cursor: "pointer",
              fontSize: "0.875rem",
            }}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default JahizErrorBoundary;
