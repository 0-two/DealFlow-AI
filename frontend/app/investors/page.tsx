'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { investorsAPI } from '@/lib/api';
import InvestorCard from '@/components/Investors/InvestorCard';
import InvestorSearch from '@/components/Investors/InvestorSearch';
import Header from '@/components/Layout/Header';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import { LanguageCode } from '@/lib/types';
import { Filter } from 'lucide-react';

export default function InvestorsPage() {
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('en');
  const [filters, setFilters] = useState({
    sector: '',
    location: '',
    stage: '',
  });
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['investors', filters],
    queryFn: () => investorsAPI.search({
      sector: filters.sector || undefined,
      location: filters.location || undefined,
      stage: filters.stage || undefined,
      limit: 50,
    }),
  });

  const filteredInvestors = data?.investors.filter((investor) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      investor.name.toLowerCase().includes(query) ||
      investor.focus_areas.some(area => area.toLowerCase().includes(query))
    );
  }) || [];

  return (
    <ProtectedRoute>
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header 
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
      />

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Discover Investors
          </h1>
          <p className="text-gray-600">
            Find the perfect investors for your startup
          </p>
        </div>

        <InvestorSearch
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
            Error loading investors. Please try again.
          </div>
        )}

        {!isLoading && !error && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-gray-600">
                Found {filteredInvestors.length} investors
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredInvestors.map((investor, index) => (
                <InvestorCard key={index} investor={investor} />
              ))}
            </div>

            {filteredInvestors.length === 0 && (
              <div className="text-center py-20">
                <Filter className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  No investors found
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
    </ProtectedRoute>
  );
}
