/**
 * Type definitions for Regulatory Intelligence Assistant API
 */

// Search types
export interface SearchResult {
  id: string;
  score: number;
  source: Record<string, any>;
  highlights?: Record<string, string[]>;
}

export interface SearchResponse {
  success: boolean;
  hits: SearchResult[];
  total: number;
  max_score?: number;
  search_type: string;
  processing_time_ms: number;
}

// Regulation types
export interface RegulationSection {
  id: string;
  number: string;
  title: string;
  content: string;
}

export interface RegulationDetail {
  success: boolean;
  id: string;
  title: string;
  citation: string | null;
  jurisdiction: string;
  authority: string;
  effective_date: string | null;
  status: string;
  full_text: string;
  sections: RegulationSection[];
}

// RAG/Q&A types
export interface Citation {
  text: string;
  document_id: string | null;
  document_title: string | null;
  section: string | null;
  confidence: number;
}

export interface SourceDocument {
  id: string;
  title: string;
  citation: string | null;
  section_number: string | null;
  score: number;
  content_preview: string | null;
}

export interface AnswerResponse {
  success: boolean;
  question: string;
  answer: string;
  citations: Citation[];
  confidence_score: number;
  source_documents: SourceDocument[];
  intent: string | null;
  processing_time_ms: number;
  cached: boolean;
  metadata: Record<string, any>;
}

// Query analysis types
export interface Entity {
  text: string;
  entity_type: string;
  normalized: string;
  confidence: number;
  start_pos: number;
  end_pos: number;
  context: string | null;
  metadata: Record<string, any> | null;
}

export interface QueryAnalysis {
  success: boolean;
  original_query: string;
  normalized_query: string;
  intent: string;
  intent_confidence: number;
  question_type: string | null;
  keywords: string[];
  entities: Entity[];
  filters: Record<string, any>;
  entity_summary: Record<string, number>;
}

// Compliance types
export interface ComplianceIssue {
  severity: string;
  field: string;
  message: string;
  suggestion: string | null;
  citation: string | null;
}

export interface ComplianceReport {
  success: boolean;
  status: string;
  issues: ComplianceIssue[];
  recommendations: string[];
  next_steps: string[];
  confidence_score: number;
  processing_time_ms: number;
}

export interface FieldValidationResponse {
  success: boolean;
  valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

// Entity extraction types
export interface EntityExtractionResponse {
  success: boolean;
  entities: Entity[];
  entity_count: number;
  entity_summary: Record<string, number>;
  processing_time_ms: number;
}
