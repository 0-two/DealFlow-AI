'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { trendsAPI } from '@/lib/api';
import Header from '@/components/Layout/Header';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import TrendChart from '@/components/Trends/TrendChart';
import { LanguageCode } from '@/lib/types';
import { TrendingUp, Calendar, DollarSign, Target } from 'lucide-react';

export default function TrendsPage() {
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('en');
  const [selectedSector, setSelectedSector] = useState('fintech');
  const [selectedYear, setSelectedYear] = useState(2024);

  const { data: sectorData, isLoading: sectorLoading } = useQuery({
    queryKey: ['sector-trends', selectedSector, selectedYear],
    queryFn: () => trendsAPI.getSectorTrends(selectedSector, selectedYear),
  });

  const { data: timelineData, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline-trends'],
    queryFn: () => trendsAPI.getTimeline('2024-01-01', '2024-12-31'),
  });

  const SECTORS = [
    'Fintech', 'Edtech', 'Healthtech', 'E-commerce', 
    'SaaS', 'AI/ML', 'Agritech', 'Logistics'
  ];

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
            Funding Trends
          </h1>
          <p className="text-gray-600">
            Insights and analytics on Indian startup ecosystem
          </p>
        </div>

        {/* Overview Cards */}
        {sectorData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Total Funding</p>
              <p className="text-2xl font-bold text-gray-900">
                ₹{sectorData.total_funding.toFixed(2)} Cr
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-8 h-8 text-indigo-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Total Deals</p>
              <p className="text-2xl font-bold text-gray-900">
                {sectorData.deal_count}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-8 h-8 text-purple-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Avg Deal Size</p>
              <p className="text-2xl font-bold text-gray-900">
                ₹{sectorData.average_deal_size.toFixed(2)} Cr
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <Calendar className="w-8 h-8 text-orange-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Unique Investors</p>
              <p className="text-2xl font-bold text-gray-900">
                {sectorData.unique_investors}
              </p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sector
              </label>
              <select
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
              >
                {SECTORS.map((sector) => (
                  <option key={sector} value={sector.toLowerCase()}>
                    {sector}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Year
              </label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
              >
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
                <option value={2022}>2022</option>
              </select>
            </div>
          </div>
        </div>

        {/* Timeline Chart */}
        {timelineData && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Funding Timeline
            </h2>
            <TrendChart data={timelineData.timeline} />
          </div>
        )}

        {/* Top Deals */}
        {sectorData && sectorData.top_deals && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Top Deals in {selectedSector.charAt(0).toUpperCase() + selectedSector.slice(1)}
            </h2>
            <div className="space-y-4">
              {sectorData.top_deals.map((deal: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{deal.startup}</h3>
                    <p className="text-sm text-gray-600">
                      {deal.stage} • {deal.date}
                    </p>
                    {deal.investors && deal.investors.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        {deal.investors.join(', ')}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-indigo-600">
                      ₹{deal.amount} Cr
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
    </ProtectedRoute>
  );
}
