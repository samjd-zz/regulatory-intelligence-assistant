import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { LoadingSpinnerProps } from '@/types'

export function LoadingSpinner({ 
  size = 'md', 
  message 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div 
      className="flex flex-col items-center justify-center gap-3"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <Loader2 
        className={cn(
          'animate-spin text-primary-500',
          sizeClasses[size]
        )}
        aria-hidden="true"
      />
      {message && (
        <p className="text-sm text-gray-600">
          {message}
        </p>
      )}
      <span className="sr-only">Loading...</span>
    </div>
  )
}
