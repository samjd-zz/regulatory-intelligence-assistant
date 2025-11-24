import { create } from 'zustand'
import type { SearchResult, FilterState, SearchResponse } from '@/types'
import { searchRegulations } from '@/services/api'

interface SearchState {
  query: string
  results: SearchResult[]
  filters: FilterState
  loading: boolean
  error: string | null
  total: number
  processingTime: number

  // Actions
  setQuery: (query: string) => void
  setResults: (results: SearchResult[]) => void
  setFilters: (filters: FilterState) => void
  updateFilters: (filters: Partial<FilterState>) => void
  clearFilters: () => void
  search: (query: string) => Promise<void>
  clearResults: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useSearchStore = create<SearchState>((set, get) => ({
  query: '',
  results: [],
  filters: {},
  loading: false,
  error: null,
  total: 0,
  processingTime: 0,

  setQuery: (query) => set({ query }),

  setResults: (results) => set({ results }),

  setFilters: (filters) => set({ filters }),

  updateFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    })),

  clearFilters: () => set({ filters: {} }),

  search: async (query: string) => {
    set({ loading: true, error: null, query })

    try {
      const response: SearchResponse = await searchRegulations({
        query,
        filters: get().filters,
        limit: 20,
      })

      // Transform SearchHit[] to SearchResult[] for UI
      const transformedResults: SearchResult[] = response.hits.map((hit) => ({
        id: hit.id,
        title: hit.source.title,
        snippet: hit.source.summary || hit.source.content?.substring(0, 300) || '',
        citation: hit.source.citation || hit.source.legislation_name || 'N/A',
        confidence: hit.score,
        relevance_score: hit.score,
        effective_date: hit.source.effective_date || '',
        jurisdiction: hit.source.jurisdiction || 'N/A',
        document_type: hit.source.document_type,
        section_number: hit.source.section_number,
      }))

      set({
        results: transformedResults,
        total: response.total,
        processingTime: response.processing_time_ms,
        loading: false,
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Search failed',
        loading: false,
        results: [],
      })
    }
  },

  clearResults: () =>
    set({
      results: [],
      query: '',
      total: 0,
      processingTime: 0,
      error: null,
    }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),
}))
