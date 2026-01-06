'use client';

import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Translation cache to avoid repeated API calls
const translationCache: Record<string, Record<string, string>> = {};

export interface TranslationStrings {
  [key: string]: string;
}

// Default English strings
const defaultStrings: TranslationStrings = {
  // Common
  'common.loading': 'Loading...',
  'common.submit': 'Submit',
  'common.cancel': 'Cancel',
  'common.success': 'Success!',
  'common.error': 'Error',
  'common.search': 'Search',
  
  // Role Select
  'role.welcome': 'Welcome to Funding Intelligence',
  'role.subtitle': 'Find your perfect match in the startup ecosystem',
  'role.founder': "I'm a Founder",
  'role.investor': "I'm an Investor",
  'role.founder_desc': 'Upload your pitch deck or startup details to find investors who match your vision.',
  'role.investor_desc': 'Share your investment thesis and discover startups that align with your portfolio.',
  'role.upload_pitch': 'Upload pitch decks',
  'role.ai_investor_match': 'AI-powered investor matching',
  'role.personalized_recs': 'Get personalized recommendations',
  'role.multilingual': 'Multilingual support',
  'role.define_thesis': 'Define investment thesis',
  'role.ai_startup_match': 'AI-powered startup matching',
  'role.discover_opps': 'Discover emerging opportunities',
  
  // Founder Upload
  'founder.title': 'Upload Your Pitch Deck',
  'founder.subtitle': 'Let AI find the perfect investors for your startup',
  'founder.upload_mode': 'Upload Pitch Deck',
  'founder.manual_mode': 'Enter Details Manually',
  'founder.drop_file': 'Drop your pitch deck here or click to browse',
  'founder.choose_file': 'Choose PDF File',
  'founder.startup_name': 'Startup Name',
  'founder.founder_name': 'Founder Name',
  'founder.sector': 'Sector',
  'founder.stage': 'Stage',
  'founder.location': 'Location',
  'founder.funding_amount': 'Funding Amount (₹ Crores)',
  'founder.description': 'Description',
  'founder.problem': 'Problem Statement',
  'founder.solution': 'Solution',
  'founder.traction': 'Traction',
  'founder.email': 'Contact Email',
  'founder.website': 'Website',
  'founder.upload_button': 'Upload & Find Investors',
  'founder.submit_button': 'Submit & Find Investors',
  'founder.processing': 'Processing...',
  'founder.matched_investors': 'Recommended Investors',
  'founder.your_profile': 'Your Startup Profile',
  'founder.match_reason': 'Why this is a good match:',
  'founder.focus_areas': 'Focus Areas',
  'founder.ticket_size': 'Ticket Size',
  'founder.portfolio': 'Portfolio',
  'founder.contact': 'Contact',
  'founder.visit_website': 'Visit Website',
  'founder.upload_another': 'Upload Another',
  'founder.remove': 'Remove',
  'founder.select_sector': 'Select Sector',
  'founder.select_stage': 'Select Stage',
  
  // Investor Thesis
  'investor.title': 'Define Your Investment Thesis',
  'investor.subtitle': 'Let AI find startups that align with your investment strategy',
  'investor.name': 'Investor/Firm Name',
  'investor.thesis': 'Investment Thesis',
  'investor.sectors': 'Focus Sectors (comma-separated)',
  'investor.stages': 'Stages (comma-separated)',
  'investor.geographies': 'Geographies (comma-separated)',
  'investor.portfolio': 'Portfolio Companies (comma-separated)',
  'investor.ticket_min': 'Min Ticket Size (₹ Crores)',
  'investor.ticket_max': 'Max Ticket Size (₹ Crores)',
  'investor.criteria': 'Investment Criteria',
  'investor.submit_button': 'Submit & Find Startups',
  'investor.finding': 'Finding Startups...',
  'investor.matched_startups': 'Recommended Startups',
  'investor.your_profile': 'Your Investment Profile',
  'investor.contact_founder': 'Contact Founder',
  'investor.submit_another': 'Submit Another Thesis',
  
  // Match Results
  'match.score': 'Match Score',
  'match.source': 'Source',
  'match.database': 'Database',
  'match.found_investors': 'Matching Investors',
  'match.found_startups': 'Matching Startups',
  
  // Navigation
  'nav.for_founders': 'For Founders',
  'nav.for_investors': 'For Investors',
  'nav.ai_chat': 'AI Chat',
};

export function useTranslation(initialLanguage: string = 'en') {
  const [language, setLanguage] = useState(initialLanguage);
  const [translations, setTranslations] = useState<TranslationStrings>(defaultStrings);
  const [isTranslating, setIsTranslating] = useState(false);

  // Translate a single string
  const translateText = useCallback(async (text: string, targetLang: string): Promise<string> => {
    if (targetLang === 'en') return text;
    
    // Check cache first
    if (translationCache[targetLang]?.[text]) {
      return translationCache[targetLang][text];
    }

    try {
      const response = await axios.post(`${API_URL}/api/query/translate`, {
        text,
        target_language: targetLang,
      });
      
      const translated = response.data.translated_text || text;
      
      // Cache the result
      if (!translationCache[targetLang]) {
        translationCache[targetLang] = {};
      }
      translationCache[targetLang][text] = translated;
      
      return translated;
    } catch (error) {
      console.error('Translation error:', error);
      return text;
    }
  }, []);

  // Translate all UI strings when language changes
  const translateAllStrings = useCallback(async (targetLang: string) => {
    if (targetLang === 'en') {
      setTranslations(defaultStrings);
      return;
    }

    setIsTranslating(true);
    
    try {
      const translatedStrings: TranslationStrings = {};
      const keys = Object.keys(defaultStrings);
      
      // Batch translate to reduce API calls
      const batchSize = 10;
      for (let i = 0; i < keys.length; i += batchSize) {
        const batch = keys.slice(i, i + batchSize);
        const promises = batch.map(async (key) => {
          const translated = await translateText(defaultStrings[key], targetLang);
          return { key, translated };
        });
        
        const results = await Promise.all(promises);
        results.forEach(({ key, translated }) => {
          translatedStrings[key] = translated;
        });
      }
      
      setTranslations(translatedStrings);
    } catch (error) {
      console.error('Failed to translate strings:', error);
      setTranslations(defaultStrings);
    } finally {
      setIsTranslating(false);
    }
  }, [translateText]);

  // Handle language change
  const changeLanguage = useCallback(async (newLang: string) => {
    setLanguage(newLang);
    localStorage.setItem('selectedLanguage', newLang);
    await translateAllStrings(newLang);
  }, [translateAllStrings]);

  // Load saved language on mount
  useEffect(() => {
    const savedLang = localStorage.getItem('selectedLanguage') || 'en';
    if (savedLang !== 'en') {
      setLanguage(savedLang);
      translateAllStrings(savedLang);
    }
  }, [translateAllStrings]);

  // Get translation by key
  const t = useCallback((key: string): string => {
    return translations[key] || defaultStrings[key] || key;
  }, [translations]);

  return {
    language,
    changeLanguage,
    t,
    translateText,
    isTranslating,
  };
}
