export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  language: string;
  sources?: Source[];
  timestamp: Date;
}

export interface WebSource {
  title: string;
  url: string;
  confidence: number;
  snippet: string;
}

export interface Source {
  id?: number;
  title: string;
  snippet: string;
  type?: 'article' | 'report' | 'policy' | 'database' | 'web';
  url: string;
  date?: string;
  score?: number;
  verified?: boolean;
  verification_confidence?: number;
  supporting_web_sources?: WebSource[];
  published_date?: string;
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
    verified_sources_count?: number;
    source_verification_enabled?: boolean;
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
  investment_stages?: string[];
  number_of_investments?: number;
  number_of_exits?: number;
  description?: string;
  founding_year?: number;
  partner_name?: string;
  twitter?: string;
  linkedin?: string;
}

export interface WebInsight {
  title: string;
  url: string;
  snippet: string;
  score?: number;
}

export interface InvestorDetailResponse {
  investor: Investor;
  web_insights: WebInsight[];
  ai_summary?: string;
  recent_news: {
    title: string;
    url: string;
    snippet: string;
    date?: string;
  }[];
}

export interface Startup {
  name: string;
  sector: string;
  stage: string;
  location: string;
  description: string;
  problem_statement?: string;
  solution?: string;
  business_model?: string;
  market_size?: string;
  traction?: string;
  funding_amount?: number;
  team_size?: number;
  revenue?: number;
  contact?: {
    email: string;
    website: string;
  };
  founder_name?: string;
  investors?: string;
  total_funding?: string;
  last_funding_date?: string;
  year_founded?: number;
  funding_status?: string;
  twitter?: string;
  linkedin?: string;
  facebook?: string;
}

export interface StartupDetailResponse {
  startup: Startup;
  web_insights: WebInsight[];
  ai_summary?: string;
  recent_news: {
    title: string;
    url: string;
    snippet: string;
    date?: string;
  }[];
  funding_history: {
    title: string;
    url: string;
    snippet: string;
  }[];
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
