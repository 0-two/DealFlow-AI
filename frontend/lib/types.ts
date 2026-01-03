export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  language: string;
  sources?: Source[];
  timestamp: Date;
}

export interface Source {
  id: number;
  title: string;
  snippet: string;
  type: 'article' | 'report' | 'policy' | 'database';
  url?: string;
  date?: string;
  score?: number;
}

export interface QueryRequest {
  query: string;
  language?: string;
  filters?: Record<string, any>;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  language: string;
  metadata: {
    retrieved_count: number;
    reranked_count: number;
  };
}

export interface Investor {
  name: string;
  type: string;
  focus_areas: string[];
  location: string;
  ticket_size: {
    min: number;
    max: number;
  };
  contact?: {
    email: string;
    website: string;
  };
  portfolio?: string[];
  score?: number;
}

export interface FundingDeal {
  startup: string;
  amount: number;
  stage: string;
  sector: string;
  date: string;
  investors: string[];
}

export interface TrendData {
  month: string;
  total_funding: number;
  deal_count: number;
  average_deal_size: number;
}

export const LANGUAGES = {
  en: 'English',
  hi: 'हिंदी',
  ta: 'தமிழ்',
  te: 'తెలుగు',
  kn: 'ಕನ್ನಡ',
  bn: 'বাংলা',
  mr: 'मराठी',
  gu: 'ગુજરાતી',
} as const;

export type LanguageCode = keyof typeof LANGUAGES;

/**
 * Common types
 */
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version?: string;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}
