import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, UserPreferences } from '@/types'

interface UserState {
  user: User | null
  preferences: UserPreferences
  recentSearches: string[]
  savedRegulations: string[]

  // Actions
  setUser: (user: User | null) => void
  updatePreferences: (prefs: Partial<UserPreferences>) => void
  addRecentSearch: (query: string) => void
  clearRecentSearches: () => void
  toggleSavedRegulation: (id: string) => void
}

const defaultPreferences: UserPreferences = {
  theme: 'auto',
  language: 'en',
  date_format: 'YYYY-MM-DD',
  results_per_page: 20,
  default_jurisdiction: ['federal'],
  notifications_enabled: true,
  notification_frequency: 'daily',
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      preferences: defaultPreferences,
      recentSearches: [],
      savedRegulations: [],

      setUser: (user) => set({ user }),

      updatePreferences: (prefs) =>
        set((state) => ({
          preferences: { ...state.preferences, ...prefs },
        })),

      addRecentSearch: (query) =>
        set((state) => {
          const searches = [query, ...state.recentSearches.filter((q) => q !== query)]
          return {
            recentSearches: searches.slice(0, 10), // Keep only last 10
          }
        }),

      clearRecentSearches: () => set({ recentSearches: [] }),

      toggleSavedRegulation: (id) =>
        set((state) => {
          const saved = state.savedRegulations.includes(id)
          return {
            savedRegulations: saved
              ? state.savedRegulations.filter((r) => r !== id)
              : [...state.savedRegulations, id],
          }
        }),
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({
        preferences: state.preferences,
        recentSearches: state.recentSearches,
        savedRegulations: state.savedRegulations,
      }),
    }
  )
)
