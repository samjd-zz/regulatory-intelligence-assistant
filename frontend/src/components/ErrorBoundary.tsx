import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
    // Reload the page to reset the app state
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>

            <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">
              Something went wrong
            </h1>

            <p className="text-gray-600 text-center mb-6">
              We're sorry, but something unexpected happened. The error has been
              logged and we'll look into it.
            </p>

            {this.state.error && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
                <p className="text-sm font-mono text-gray-700 break-all">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            <button
              onClick={this.handleReset}
              className="w-full bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center gap-2 font-medium"
            >
              <RefreshCw className="w-5 h-5" />
              Return to Home
            </button>

            {import.meta.env.DEV && this.state.errorInfo && (
              <details className="mt-6">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  Error Details (Development Only)
                </summary>
                <pre className="mt-2 text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-auto max-h-64">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
