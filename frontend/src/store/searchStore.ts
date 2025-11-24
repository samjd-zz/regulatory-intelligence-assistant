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

      set({
        results: response.results,
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
