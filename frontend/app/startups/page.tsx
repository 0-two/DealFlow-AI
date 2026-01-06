'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { startupsAPI } from '@/lib/api';
import StartupCard from '@/components/Startups/StartupCard';
import StartupSearch from '@/components/Startups/StartupSearch';
import Header from '@/components/Layout/Header';
import { LanguageCode } from '@/lib/types';
import { Filter } from 'lucide-react';

export default function StartupsPage() {
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('en');
  const [filters, setFilters] = useState({
    sector: '',
    location: '',
    stage: '',
  });
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['startups', filters, searchQuery],
    queryFn: () => startupsAPI.search({
      query: searchQuery || 'startups',
      focus_sectors: filters.sector || undefined,
      stages: filters.stage || undefined,
      location: filters.location || undefined,
    }),
  });

  const startups = data?.matches || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header 
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
      />

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Discover Startups
          </h1>
          <p className="text-gray-600">
            Find promising startups for your investment portfolio
          </p>
        </div>

        <StartupSearch
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          filters={filters}
          onFiltersChange={setFilters}
        />

        {isLoading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            Error loading startups. Please try again.
          </div>
        )}

        {!isLoading && !error && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-gray-600">
                Found {startups.length} startups
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {startups.map((startup: any, index: number) => (
                <StartupCard key={index} startup={startup} />
              ))}
            </div>

            {startups.length === 0 && (
              <div className="text-center py-20">
                <Filter className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  No startups found
                </h3>
                <p className="text-gray-500">
                  Try adjusting your search filters
                </p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
