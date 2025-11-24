import axios, { AxiosError } from 'axios'
import type {
  SearchQuery,
  SearchResponse,
  QARequest,
  QAResponse,
  ComplianceCheckRequest,
  ComplianceCheckResponse,
  Regulation,
  ValidationResult,
} from '@/types'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth tokens
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============================================================================
// Search API
// ============================================================================

export async function searchRegulations(
  query: SearchQuery
): Promise<SearchResponse> {
  const { data } = await api.post('/search', query)
  return data
}

export async function getSuggestions(query: string): Promise<string[]> {
  const { data } = await api.get('/search/suggestions', {
    params: { q: query },
  })
  return data.suggestions || []
}

// ============================================================================
// Q&A / RAG API
// ============================================================================

export async function askQuestion(request: QARequest): Promise<QAResponse> {
  const { data } = await api.post('/rag/ask', request)
  return data
}

// ============================================================================
// Regulation API
// ============================================================================

export async function getRegulation(id: string): Promise<Regulation> {
  const { data } = await api.get(`/documents/${id}`)
  return data
}

export async function getRelatedRegulations(id: string): Promise<Regulation[]> {
  const { data } = await api.get(`/graph/related/${id}`)
  return data.related || []
}

// ============================================================================
// Compliance API
// ============================================================================

export async function checkCompliance(
  request: ComplianceCheckRequest
): Promise<ComplianceCheckResponse> {
  const { data } = await api.post('/compliance/check', request)
  return data
}

export async function validateField(
  programId: string,
  field: string,
  value: unknown
): Promise<ValidationResult> {
  const { data } = await api.post('/compliance/validate', {
    program_id: programId,
    field,
    value,
  })
  return data
}

// ============================================================================
// Health Check
// ============================================================================

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get('/health')
  return data
}

export default api
