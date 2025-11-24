import { Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { CitationTagProps } from '@/types'

export function CitationTag({ 
  citation, 
  onClick, 
  variant = 'default' 
}: CitationTagProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    await navigator.clipboard.writeText(citation)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleClick = () => {
    if (onClick) onClick()
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded font-mono text-xs',
        variant === 'compact' ? 'px-1.5 py-0.5' : 'px-2 py-1',
        'bg-gray-100 text-gray-800 border border-gray-300',
        onClick && 'cursor-pointer hover:bg-gray-200 hover:border-gray-400',
        'transition-colors'
      )}
      onClick={handleClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          onClick()
        }
      }}
      aria-label={`Citation: ${citation}`}
    >
      <span className="select-all">{citation}</span>
      <button
        onClick={handleCopy}
        className="ml-1 p-0.5 rounded hover:bg-gray-300 transition-colors"
        aria-label="Copy citation"
        title="Copy citation"
        type="button"
      >
        {copied ? (
          <Check className="w-3 h-3 text-green-600" aria-label="Copied" />
        ) : (
          <Copy className="w-3 h-3" aria-hidden="true" />
        )}
      </button>
    </span>
  )
}
