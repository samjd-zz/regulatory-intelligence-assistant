/**
 * API Client for Regulatory Intelligence Assistant
 * Handles HTTP requests to the FastAPI backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as dotenv from 'dotenv';
import type {
  SearchResponse,
  RegulationDetail,
  AnswerResponse,
  QueryAnalysis,
  ComplianceReport,
  FieldValidationResponse,
  EntityExtractionResponse,
} from './types.js';

// Load environment variables
dotenv.config();

/**
 * API Client class
 */
export class RegulatoryAPIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.API_BASE_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: parseInt(process.env.API_TIMEOUT || '30000'),
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return Promise.reject(this.formatError(error));
      }
    );
  }

  /**
   * Format API errors for better readability
   */
  private formatError(error: AxiosError): Error {
    if (error.response) {
      // Server responded with error status
      const message = `API Error ${error.response.status}: ${
        (error.response.data as any)?.detail || error.message
      }`;
      return new Error(message);
    } else if (error.request) {
      // No response received
      return new Error(
        `No response from API server at ${this.baseURL}. Is the backend running?`
      );
    } else {
      // Request setup error
      return new Error(`Request error: ${error.message}`);
    }
  }

  /**
   * Health check - verify API is accessible
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  }

  // ============================================================================
  // SEARCH TOOLS
  // ============================================================================

  /**
   * Search regulations using hybrid search
   */
  async searchRegulations(
    query: string,
    filters?: Record<string, any>,
    size: number = 10
  ): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/api/search/hybrid', {
      query,
      filters: filters || {},
      size,
      from: 0,
      keyword_weight: 0.5,
      vector_weight: 0.5,
      parse_query: true,
    });
    return response.data;
  }

  /**
   * Get detailed regulation information
   */
  async getRegulationDetail(regulationId: string): Promise<RegulationDetail> {
    const response = await this.client.get<RegulationDetail>(
      `/api/search/regulation/${regulationId}`
    );
    return response.data;
  }

  // ============================================================================
  // Q&A TOOLS
  // ============================================================================

  /**
   * Ask a legal question and get AI-generated answer with citations
   */
  async askLegalQuestion(
    question: string,
    jurisdiction?: string,
    numContextDocs: number = 5
  ): Promise<AnswerResponse> {
    const filters: Record<string, any> = {};
    if (jurisdiction) {
      filters.jurisdiction = jurisdiction;
    }

    const response = await this.client.post<AnswerResponse>('/api/rag/ask', {
      question,
      filters,
      num_context_docs: numContextDocs,
      use_cache: true,
      temperature: 0.3,
      max_tokens: 1024,
    });
    return response.data;
  }

  /**
   * Analyze a legal query without answering it
   */
  async analyzeQuery(query: string): Promise<QueryAnalysis> {
    const response = await this.client.get<QueryAnalysis>('/api/search/analyze', {
      params: {
        query,
        extract_filters: true,
      },
    });
    return response.data;
  }

  // ============================================================================
  // COMPLIANCE TOOLS
  // ============================================================================

  /**
   * Check compliance of form data against regulatory requirements
   */
  async checkCompliance(
    programId: string,
    formData: Record<string, any>,
    workflowType: string = 'application'
  ): Promise<ComplianceReport> {
    const response = await this.client.post<ComplianceReport>('/api/compliance/check', {
      program_id: programId,
      workflow_type: workflowType,
      form_data: formData,
      user_context: {},
      check_optional: false,
    });
    return response.data;
  }

  /**
   * Validate a single form field in real-time
   */
  async validateField(
    programId: string,
    fieldName: string,
    fieldValue: any,
    formContext?: Record<string, any>
  ): Promise<FieldValidationResponse> {
    const response = await this.client.post<FieldValidationResponse>(
      '/api/compliance/validate-field',
      {
        program_id: programId,
        field_name: fieldName,
        field_value: fieldValue,
        form_context: formContext || {},
      }
    );
    return response.data;
  }

  // ============================================================================
  // NLP TOOLS
  // ============================================================================

  /**
   * Extract legal entities from text
   */
  async extractLegalEntities(
    text: string,
    entityTypes?: string[]
  ): Promise<EntityExtractionResponse> {
    const response = await this.client.post<EntityExtractionResponse>(
      '/api/nlp/extract-entities',
      {
        text,
        entity_types: entityTypes || undefined,
      }
    );
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new RegulatoryAPIClient();
