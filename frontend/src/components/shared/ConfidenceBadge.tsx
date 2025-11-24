import { Target } from 'lucide-react'
import { cn, getConfidenceLabel, getConfidenceColor } from '@/lib/utils'
import type { ConfidenceBadgeProps } from '@/types'

export function ConfidenceBadge({ 
  score, 
  showLabel = true, 
  size = 'md' 
}: ConfidenceBadgeProps) {
  const label = getConfidenceLabel(score)
  const colorClass = getConfidenceColor(score)
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  }
  
  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }
  
  const bgClass = score >= 0.8 
    ? 'bg-green-100' 
    : score >= 0.5 
    ? 'bg-yellow-100' 
    : 'bg-orange-100'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium',
        sizeClasses[size],
        bgClass,
        colorClass
      )}
      role="status"
      aria-label={`Confidence score: ${Math.round(score * 100)}%`}
      title={`Confidence: ${label} (${Math.round(score * 100)}%)`}
    >
      <Target className={iconSizes[size]} aria-hidden="true" />
      {showLabel && <span>{label}</span>}
    </span>
  )
}
