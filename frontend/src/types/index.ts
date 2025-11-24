// ============================================================================
// Core Types
// ============================================================================

export interface User {
  id: string
  email: string
  role: string
  department?: string
  preferences: UserPreferences
  created_at: string
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: 'en' | 'fr'
  date_format: string
  results_per_page: number
  default_jurisdiction?: string[]
  notifications_enabled: boolean
  notification_frequency: 'realtime' | 'daily' | 'weekly'
}

// ============================================================================
// Search Types
// ============================================================================

export interface SearchQuery {
  query: string
  filters?: FilterState
  limit?: number
}

export interface FilterState {
  jurisdiction?: string[]
  date_range?: { start?: string; end?: string }
  document_type?: string[]
  programs?: string[]
}

export interface SearchResult {
  id: string
  title: string
  snippet: string
  citation: string
  confidence: number
  relevance_score: number
  effective_date: string
  jurisdiction: string
  document_type: 'act' | 'regulation' | 'policy'
  section_number?: string
}

export interface SearchResponse {
  query_id: string
  results: SearchResult[]
  total: number
  processing_time_ms: number
}

export interface Suggestion {
  id: string
  text: string
  type: 'regulation' | 'program' | 'query'
  metadata?: Record<string, unknown>
}

// ============================================================================
// Regulation Types
// ============================================================================

export interface Regulation {
  id: string
  title: string
  jurisdiction: string
  authority: string
  effective_date: string
  status: 'active' | 'amended' | 'repealed'
  full_text: string
  metadata: RegulationMetadata
  sections?: Section[]
}

export interface RegulationMetadata {
  citation: string
  document_type: string
  tags?: string[]
  related_regulations?: string[]
}

export interface Section {
  id: string
  regulation_id: string
  section_number: string
  title: string
  content: string
  metadata?: Record<string, unknown>
}

// ============================================================================
// Q&A / Chat Types
// ============================================================================

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  confidence?: number
  timestamp: Date
}

export interface Citation {
  regulation_id: string
  title: string
  section: string
  citation_text: string
}

export interface QARequest {
  question: string
  context?: {
    program?: string
    user_type?: string
    [key: string]: unknown
  }
}

export interface QAResponse {
  answer: string
  confidence: 'high' | 'medium' | 'low'
  sources: {
    regulation: string
    section: string
    citation: string
  }[]
  related_questions?: string[]
}

// ============================================================================
// Compliance Types
// ============================================================================

export interface ComplianceCheckRequest {
  form_data: Record<string, unknown>
  program_id: string
}

export interface ComplianceCheckResponse {
  compliant: boolean
  issues: Issue[]
  passed_checks: string[]
  confidence: number
  generated_at: string
}

export interface Issue {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  field: string
  description: string
  regulation: string
  suggestion: string
}

export interface ValidationResult {
  valid: boolean
  errors?: ValidationError[]
  warnings?: ValidationWarning[]
}

export interface ValidationError {
  field: string
  message: string
  regulation: string
  severity: 'critical' | 'high' | 'medium'
}

export interface ValidationWarning {
  field: string
  message: string
  suggestion: string
}

// ============================================================================
// Workflow Types
// ============================================================================

export interface WorkflowSession {
  id: string
  user_id: string
  workflow_type: string
  current_step: number
  state: Record<string, unknown>
  status: 'active' | 'complete' | 'cancelled'
  started_at: string
  completed_at?: string
  steps: WorkflowStep[]
}

export interface WorkflowStep {
  id: string
  step_number: number
  title: string
  description: string
  fields: WorkflowField[]
  validation_rules?: Record<string, unknown>
}

export interface WorkflowField {
  name: string
  type: 'text' | 'number' | 'date' | 'select' | 'file'
  label: string
  required: boolean
  options?: string[]
  validation?: Record<string, unknown>
}

// ============================================================================
// Alert Types
// ============================================================================

export interface Alert {
  id: string
  subscription_id: string
  change_type: string
  regulation_id: string
  summary: string
  created_at: string
  read: boolean
}

export interface AlertSubscription {
  id: string
  user_id: string
  jurisdiction: string
  topics: string[]
  frequency: 'realtime' | 'daily' | 'weekly'
  active: boolean
}

// ============================================================================
// API Response Types
// ============================================================================

export interface APIResponse<T> {
  data: T
  status: number
  message?: string
}

export interface APIError {
  error: string
  detail?: string
  status: number
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface ConfidenceBadgeProps {
  score: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export interface CitationTagProps {
  citation: string
  onClick?: () => void
  variant?: 'default' | 'compact'
}

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}
