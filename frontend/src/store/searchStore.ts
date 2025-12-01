import { create } from 'zustand'
import type { SearchResult, FilterState, SearchResponse } from '@/types'
import { searchRegulations } from '@/services/api'
// import { useLanguageStore } from './languageStore' // Disabled until language field is populated in documents

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
      // Note: Language filtering disabled until documents have language field populated
      // const currentLanguage = useLanguageStore.getState().language
      // const filters = { ...get().filters, language: currentLanguage }
      
      const response: SearchResponse = await searchRegulations({
        query,
        filters: get().filters,
        limit: 20,
      })

      // Transform SearchHit[] to SearchResult[] for UI
      const transformedResults: SearchResult[] = response.hits.map((hit) => ({
        id: String(hit.source.regulation_id || hit.id), // Use regulation_id for sections, fallback to id for regulations
        title: String(hit.source.regulation_title || hit.source.title || 'Untitled'), // Use regulation title if available
        snippet: hit.source.summary || hit.source.content?.substring(0, 300) || '',
        citation: String(hit.source.citation || hit.source.legislation_name || hit.source.authority || 'Unknown Citation'),
        confidence: hit.score,
        relevance_score: hit.score,
        effective_date: String(hit.source.effective_date || ''),
        jurisdiction: String(hit.source.jurisdiction || 'Federal'),
        document_type: String(hit.source.document_type || 'regulation'),
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
