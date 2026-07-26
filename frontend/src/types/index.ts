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

// Backend search response structure (from /api/search/hybrid)
export interface SearchHit {
  id: string
  score: number
  source: {
    title: string
    content?: string
    summary?: string
    document_type: string
    jurisdiction?: string
    program?: string
    legislation_name?: string
    citation?: string
    section_number?: string
    effective_date?: string
    status?: string
    [key: string]: unknown
  }
  highlights?: {
    [field: string]: string[]
  }
  score_breakdown?: {
    keyword: number
    vector: number
    combined: number
  }
}

export interface SearchResponse {
  success: boolean
  hits: SearchHit[]
  total: number
  max_score?: number
  search_type: string
  query_info?: {
    intent: string
    intent_confidence: number
    keywords: string[]
    entities?: Array<{
      text: string
      entity_type: string
      normalized: string
      confidence: number
    }>
  }
  processing_time_ms: number
}

// Convenience type for display
export interface SearchResult {
  id: string
  title: string
  snippet: string
  citation: string
  confidence: number
  relevance_score: number
  effective_date: string
  jurisdiction: string
  document_type: string
  section_number?: string
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

export interface RelatedDocument {
  id: string
  title: string
  type: string
}

export interface RegulationRelationships {
  regulation_id: string
  references: RelatedDocument[]
  referenced_by: RelatedDocument[]
  implements: RelatedDocument[]
  implemented_by: RelatedDocument[]
  applies_to: RelatedDocument[]
  counts: {
    references: number
    referenced_by: number
    implements: number
    implemented_by: number
    applies_to: number
  }
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
  program_id: string
  workflow_type: string
  form_data: Record<string, unknown>
  user_context?: Record<string, unknown>
  check_optional?: boolean
}

export interface ComplianceCheckResponse {
  report_id: string
  program_id: string
  workflow_type: string
  timestamp: string
  compliant: boolean
  confidence: number
  issues: Issue[]
  passed_requirements: number
  total_requirements: number
  critical_issues: number
  high_issues: number
  recommendations: string[]
  next_steps: string[]
}

export interface Issue {
  issue_id: string
  field_name: string | null
  requirement: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  regulation_citation: string | null
  regulation_id: string | null
  section_id: string | null
  suggestion: string | null
  current_value: unknown
  expected_value: unknown
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
