import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLanguageStore } from '@/store/languageStore';

/**
 * Custom hook to sync i18n language with the language store
 * This ensures that when the user toggles the language in the header,
 * both the i18n translations and the data language filter are updated
 */
export function useLanguageSync() {
  const { i18n } = useTranslation();
  const language = useLanguageStore((state) => state.language);

  useEffect(() => {
    // Sync i18n language whenever the store language changes
    if (i18n.language !== language) {
      i18n.changeLanguage(language);
    }
  }, [language, i18n]);

  // Also sync on mount in case localStorage has a saved preference
  useEffect(() => {
    const storedLanguage = useLanguageStore.getState().language;
    if (i18n.language !== storedLanguage) {
      i18n.changeLanguage(storedLanguage);
    }
  }, [i18n]);
}
