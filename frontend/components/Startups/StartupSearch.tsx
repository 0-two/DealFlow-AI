'use client';

import { Search } from 'lucide-react';

interface StartupSearchProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filters: {
    sector: string;
    location: string;
    stage: string;
  };
  onFiltersChange: (filters: any) => void;
}

export default function StartupSearch({
  searchQuery,
  onSearchChange,
  filters,
  onFiltersChange,
}: StartupSearchProps) {
  const SECTORS = [
    'Fintech',
    'Edtech',
    'Healthtech',
    'E-commerce',
    'SaaS',
    'AI/ML',
    'Agritech',
    'Logistics',
  ];

  const STAGES = [
    'Pre-Seed',
    'Seed',
    'Series A',
    'Series B',
    'Series C',
  ];

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-8">
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search startups by name, description..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sector
          </label>
          <select
            value={filters.sector}
            onChange={(e) => onFiltersChange({ ...filters, sector: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          >
            <option value="">All Sectors</option>
            {SECTORS.map((sector) => (
              <option key={sector} value={sector}>
                {sector}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Stage
          </label>
          <select
            value={filters.stage}
            onChange={(e) => onFiltersChange({ ...filters, stage: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          >
            <option value="">All Stages</option>
            {STAGES.map((stage) => (
              <option key={stage} value={stage}>
                {stage}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            placeholder="e.g., Bangalore"
            value={filters.location}
            onChange={(e) => onFiltersChange({ ...filters, location: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          />
        </div>
      </div>
    </div>
  );
}
