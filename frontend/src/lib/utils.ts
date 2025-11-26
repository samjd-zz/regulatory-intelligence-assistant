import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind CSS classes with proper precedence
 * Uses clsx for conditional classes and tailwind-merge to handle conflicts
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format date to readable string
 */
export function formatDate(date: Date | string | null | undefined): string {
  // Handle null or undefined
  if (!date) {
    return 'N/A'
  }
  
  // Convert string to Date if needed
  const d = typeof date === 'string' ? new Date(date) : date
  
  // Check if the date is valid
  if (isNaN(d.getTime())) {
    return 'N/A'
  }
  
  return new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(d)
}

/**
 * Format confidence score to label
 */
export function getConfidenceLabel(score: number): string {
  if (score >= 0.8) return 'High'
  if (score >= 0.5) return 'Medium'
  return 'Low'
}

/**
 * Format confidence score to color class
 */
export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return 'text-confidence-high'
  if (score >= 0.5) return 'text-confidence-medium'
  return 'text-confidence-low'
}

/**
 * Debounce function for search inputs
 */
export function debounce<T extends (...args: never[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: number | null = null
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait) as unknown as number
  }
}

/**
 * Truncate text to specified length
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}
