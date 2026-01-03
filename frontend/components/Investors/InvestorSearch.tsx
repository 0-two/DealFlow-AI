'use client';

import { Search, X } from 'lucide-react';

interface Props {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filters: {
    sector: string;
    location: string;
    stage: string;
  };
  onFiltersChange: (filters: any) => void;
}

const SECTORS = [
  'Fintech', 'Edtech', 'Healthtech', 'E-commerce', 
  'SaaS', 'AI/ML', 'Agritech', 'Logistics', 'Food & Beverage'
];

const LOCATIONS = [
  'Bangalore', 'Mumbai', 'Delhi NCR', 'Hyderabad', 
  'Chennai', 'Pune', 'Kolkata', 'Ahmedabad'
];

const STAGES = [
  'Pre-Seed', 'Seed', 'Series A', 'Series B', 
  'Series C', 'Growth', 'Late Stage'
];

export default function InvestorSearch({ 
  searchQuery, 
  onSearchChange, 
  filters, 
  onFiltersChange 
}: Props) {
  const hasActiveFilters = filters.sector || filters.location || filters.stage;

  const clearFilters = () => {
    onFiltersChange({ sector: '', location: '', stage: '' });
    onSearchChange('');
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 mb-8">
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by investor name or focus area..."
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
              <option key={sector} value={sector}>{sector}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <select
            value={filters.location}
            onChange={(e) => onFiltersChange({ ...filters, location: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          >
            <option value="">All Locations</option>
            {LOCATIONS.map((location) => (
              <option key={location} value={location}>{location}</option>
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
              <option key={stage} value={stage}>{stage}</option>
            ))}
          </select>
        </div>
      </div>

      {hasActiveFilters && (
        <button
          onClick={clearFilters}
          className="mt-4 flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-700"
        >
          <X className="w-4 h-4" />
          Clear all filters
        </button>
      )}
    </div>
  );
}
