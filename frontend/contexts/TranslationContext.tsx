'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { useTranslation } from '@/hooks/useTranslation';

interface TranslationContextType {
  language: string;
  changeLanguage: (lang: string) => Promise<void>;
  t: (key: string) => string;
  translateText: (text: string, targetLang: string) => Promise<string>;
  isTranslating: boolean;
}

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

export function TranslationProvider({ children }: { children: ReactNode }) {
  const translation = useTranslation();

  return (
    <TranslationContext.Provider value={translation}>
      {children}
    </TranslationContext.Provider>
  );
}

export function useTranslationContext() {
  const context = useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslationContext must be used within a TranslationProvider');
  }
  return context;
}
