import axios, { AxiosError } from 'axios';
import { QueryRequest, QueryResponse, Investor, ApiError, InvestorDetailResponse, StartupDetailResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryAPI = {
  ask: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await api.post('/api/query', request);
    return response.data;
  },
  askStream: async (
    request: QueryRequest,
    onToken: (chunk: string) => void,
    onFinal?: (final: { sources?: any[]; language?: string; metadata?: any }) => void,
    onSources?: (sources: any[]) => void
  ): Promise<void> => {
    const res = await fetch(`${API_URL}/api/query/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      body: JSON.stringify(request),
    });
    if (!res.body) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        const line = part.split('\n').find((entry) => entry.startsWith('data:')) || '';
        if (!line.startsWith('data:')) continue;
        // Remove only the optional SSE delimiter space. Preserve whitespace
        // emitted by the model because it is meaningful between tokens.
        const rawData = line.slice(5);
        const data = rawData.startsWith(' ') ? rawData.slice(1) : rawData;
        if (!data) continue;
        // Try to parse JSON event
        if (data.startsWith('{')) {
          try {
            const payload = JSON.parse(data);
            if (payload.type === 'final') {
              if (onFinal) onFinal(payload);
              continue; // Don't append JSON to answer
            }
            if (payload.type === 'sources' && onSources) {
              onSources(payload.sources || []);
              continue; // Don't append JSON to answer
            }
          } catch {
            // Not valid JSON, treat as text token
          }
        }
        // Regular text token
        onToken(data);
      }
    }
  }
};

export const investorsAPI = {
  search: async (params: {
    sector?: string;
    location?: string;
    stage?: string;
    limit?: number;
  }): Promise<{ investors: Investor[]; count: number }> => {
    const response = await api.get('/api/investors/search', { params });
    return response.data;
  },
  
  recommend: async (profile: {
    name: string;
    sector: string;
    stage: string;
    location: string;
    funding_needed: number;
    description: string;
  }) => {
    const response = await api.post('/api/investors/recommend', profile);
    return response.data;
  },

  getDetails: async (investorName: string): Promise<InvestorDetailResponse> => {
    const encodedName = encodeURIComponent(investorName);
    const response = await api.get(`/api/investors/details/${encodedName}`);
    return response.data;
  },
};

export const startupsAPI = {
  search: async (params: {
    query: string;
    focus_sectors?: string;
    stages?: string;
    location?: string;
  }): Promise<{ matches: any[]; query_used?: string }> => {
    const formData = new FormData();
    formData.append('query', params.query);
    formData.append('user_context', JSON.stringify({ role: 'investor' }));
    if (params.focus_sectors) formData.append('focus_sectors', params.focus_sectors);
    if (params.stages) formData.append('stages', params.stages);
    if (params.location) formData.append('location', params.location);
    
    const response = await api.post('/api/investor-thesis/find-startups', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getDetails: async (startupName: string): Promise<StartupDetailResponse> => {
    const encodedName = encodeURIComponent(startupName);
    const response = await api.get(`/api/investor-thesis/startup-details/${encodedName}`);
    return response.data;
  },
};

export const trendsAPI = {
  getSectorTrends: async (sector: string, year: number) => {
    const response = await api.get('/api/trends/sector', {
      params: { sector, year },
    });
    return response.data;
  },
  
  getTimeline: async (start_date: string, end_date: string) => {
    const response = await api.get('/api/trends/timeline', {
      params: { start_date, end_date },
    });
    return response.data;
  },

  analyze: async (query: string, dimensions: string[]) => {
    const response = await api.post('/api/trends/analyze', {
      query,
      dimensions,
    });
    return response.data;
  },
};

export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    return {
      status: axiosError.response?.status || 500,
      message: axiosError.message || 'An error occurred',
      detail: (axiosError.response?.data as any)?.detail || undefined,
    };
  }

  return {
    status: 500,
    message: 'An unexpected error occurred',
  };
};

export default api;
