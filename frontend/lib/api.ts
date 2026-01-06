import axios, { AxiosError } from 'axios';
import { QueryRequest, QueryResponse, Investor, ApiError } from './types';

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
