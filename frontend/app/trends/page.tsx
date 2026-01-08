'use client';

import { useMemo, useState } from 'react';
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
  const [useDemo, setUseDemo] = useState(false);

  const demoData = useMemo(() => {
    const months = [
      '2024-01','2024-02','2024-03','2024-04','2024-05','2024-06',
      '2024-07','2024-08','2024-09','2024-10','2024-11','2024-12'
    ];
    const timeline = months.map((m, i) => {
      const base = 50 + (i % 4) * 15; // base oscillation
      const total = Math.round((base + Math.random() * 20) * 100) / 100; // ₹ Cr
      const deals = Math.max(3, Math.round(total / 5));
      return {
        month: m,
        total_funding: total,
        deal_count: deals,
        average_deal_size: deals ? Math.round((total / deals) * 100) / 100 : 0,
      };
    });
    const total_funding = timeline.reduce((s, t) => s + t.total_funding, 0);
    const deal_count = timeline.reduce((s, t) => s + t.deal_count, 0);
    const average_deal_size = deal_count ? total_funding / deal_count : 0;
    const top_deals = [
      { startup: 'Acme AI', amount: 120, stage: 'Series A', date: '2024-09-12', investors: ['Prime Ventures','Sequoia'] },
      { startup: 'FinNova', amount: 95, stage: 'Series B', date: '2024-06-22', investors: ['Accel','Matrix'] },
      { startup: 'HealthEdge', amount: 78, stage: 'Series A', date: '2024-03-08', investors: ['Blume','Lightspeed'] },
      { startup: 'AgriNext', amount: 64, stage: 'Pre-Series A', date: '2024-02-18', investors: ['Omidyar Network'] },
      { startup: 'LogiFlow', amount: 55, stage: 'Seed', date: '2024-05-11', investors: ['AngelList','Titan Capital'] },
    ];
    return {
      sectorData: {
        sector: selectedSector,
        year: selectedYear,
        total_funding,
        deal_count,
        average_deal_size,
        unique_investors: 25,
        top_deals,
      },
      timelineData: { timeline },
    };
  }, [selectedSector, selectedYear]);

  const { data: sectorData, isLoading: sectorLoading } = useQuery({
    queryKey: ['sector-trends', selectedSector, selectedYear],
    queryFn: () => trendsAPI.getSectorTrends(selectedSector, selectedYear),
    enabled: !useDemo,
  });

  const { data: timelineData, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline-trends'],
    queryFn: () => trendsAPI.getTimeline('2024-01-01', '2024-12-31'),
    enabled: !useDemo,
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
        {(useDemo ? demoData.sectorData : sectorData) && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Total Funding</p>
              <p className="text-2xl font-bold text-gray-900">
                ₹{(useDemo ? demoData.sectorData.total_funding : sectorData.total_funding).toFixed(2)} Cr
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-8 h-8 text-indigo-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Total Deals</p>
              <p className="text-2xl font-bold text-gray-900">
                {useDemo ? demoData.sectorData.deal_count : sectorData.deal_count}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-8 h-8 text-purple-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Avg Deal Size</p>
              <p className="text-2xl font-bold text-gray-900">
                ₹{(useDemo ? demoData.sectorData.average_deal_size : sectorData.average_deal_size).toFixed(2)} Cr
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <Calendar className="w-8 h-8 text-orange-600" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Unique Investors</p>
              <p className="text-2xl font-bold text-gray-900">
                {useDemo ? demoData.sectorData.unique_investors : sectorData.unique_investors}
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
        {(useDemo ? demoData.timelineData : timelineData) && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Funding Timeline
            </h2>
            <TrendChart data={(useDemo ? demoData.timelineData.timeline : timelineData.timeline)} />
          </div>
        )}

        {/* Top Deals */}
        {(useDemo ? demoData.sectorData : sectorData) && (useDemo ? demoData.sectorData.top_deals : sectorData.top_deals) && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Top Deals in {selectedSector.charAt(0).toUpperCase() + selectedSector.slice(1)}
            </h2>
            <div className="space-y-4">
              {(useDemo ? demoData.sectorData.top_deals : sectorData.top_deals).map((deal: any, index: number) => (
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

        {/* Empty State with Demo Toggle */}
        {(!useDemo && !sectorLoading && !timelineLoading && (!sectorData || !timelineData || (timelineData.timeline?.length || 0) === 0)) && (
          <div className="bg-white rounded-xl shadow-md p-6 mt-6 border border-dashed border-gray-300 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No trends data available</h3>
            <p className="text-gray-600 mb-4">It looks like funding deals aren’t loaded yet. You can preview with demo data or ingest real deals.</p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setUseDemo(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Use demo data
              </button>
              <a
                href="/docs/ingest"
                onClick={(e) => e.preventDefault()}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                title="Run the backend scripts to ingest data"
              >
                Ingest real data
              </a>
            </div>
          </div>
        )}
      </main>
    </div>
    </ProtectedRoute>
  );
}
