import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface LanguageState {
  language: 'en' | 'fr';
  setLanguage: (language: 'en' | 'fr') => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: 'en', // Default to English
      setLanguage: (language) => set({ language }),
    }),
    {
      name: 'language-storage', // localStorage key
    }
  )
);
