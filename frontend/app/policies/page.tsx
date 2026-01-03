'use client';

import { useState } from 'react';
import Header from '@/components/Layout/Header';
import { LanguageCode } from '@/lib/types';
import { FileText, Building, CheckCircle, Calendar, ExternalLink } from 'lucide-react';

interface Policy {
  id: string;
  scheme_name: string;
  authority: string;
  sector: string;
  description: string;
  eligibility: string[];
  benefits: string[];
  deadline?: string;
  source_url?: string;
}

// Sample policies data
const SAMPLE_POLICIES: Policy[] = [
  {
    id: '1',
    scheme_name: 'Startup India Seed Fund Scheme (SISFS)',
    authority: 'Government of India',
    sector: 'All Sectors',
    description: 'Provides financial assistance to startups for proof of concept, prototype development, product trials, market entry, and commercialization.',
    eligibility: [
      'DPIIT recognized startups',
      'Incorporated not more than 2 years ago',
      'Working towards innovation, development of products, processes, or services',
      'Should have a business model with high potential of employment generation or wealth creation'
    ],
    benefits: [
      'Up to ₹20 Lakhs for validation of Proof of Concept',
      'Up to ₹50 Lakhs for prototype development, product trials, market entry, and commercialization'
    ],
    source_url: 'https://www.startupindia.gov.in/content/sih/en/startup-scheme.html'
  },
  {
    id: '2',
    scheme_name: 'BIRAC BioNEST',
    authority: 'Biotechnology Industry Research Assistance Council',
    sector: 'Biotech / Healthcare',
    description: 'Bio-incubator supporting innovative biotech startups with infrastructure, mentorship, and funding support.',
    eligibility: [
      'Biotech and life sciences startups',
      'Early-stage companies with innovative products',
      'Teams with strong scientific background'
    ],
    benefits: [
      'State-of-the-art lab infrastructure',
      'Seed funding up to ₹50 Lakhs',
      'Mentorship and industry connections',
      'Access to specialized equipment'
    ],
    source_url: 'https://birac.nic.in/bionest.php'
  },
  {
    id: '3',
    scheme_name: 'Karnataka Elevate Program',
    authority: 'Government of Karnataka',
    sector: 'Technology',
    description: 'Provides grants to tech startups in Karnataka for product development and scaling.',
    eligibility: [
      'Startups registered in Karnataka',
      'Working on innovative tech products',
      'At least 51% of founders should be from Karnataka or settled in Karnataka'
    ],
    benefits: [
      'Grant of up to ₹50 Lakhs',
      'No equity dilution',
      'Mentorship and networking opportunities'
    ],
    deadline: '2025-03-31',
    source_url: 'https://elevate.karnataka.gov.in'
  },
  {
    id: '4',
    scheme_name: 'Pradhan Mantri MUDRA Yojana',
    authority: 'Government of India',
    sector: 'Micro Enterprises',
    description: 'Provides loans to micro and small business units to help them expand.',
    eligibility: [
      'Non-corporate, non-farm small/micro enterprises',
      'Loan requirement up to ₹10 Lakhs',
      'Income generating activity in manufacturing, trading, or service sector'
    ],
    benefits: [
      'Shishu: Up to ₹50,000',
      'Kishore: ₹50,001 to ₹5 Lakhs',
      'Tarun: ₹5,00,001 to ₹10 Lakhs',
      'No collateral required for loans up to ₹10 Lakhs'
    ],
    source_url: 'https://www.mudra.org.in'
  }
];

export default function PoliciesPage() {
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('en');
  const [selectedSector, setSelectedSector] = useState('all');
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);

  const sectors = ['all', 'All Sectors', 'Technology', 'Biotech / Healthcare', 'Micro Enterprises'];

  const filteredPolicies = SAMPLE_POLICIES.filter(policy => 
    selectedSector === 'all' || policy.sector === selectedSector
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header 
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
      />

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Government Schemes & Policies
          </h1>
          <p className="text-gray-600">
            Discover funding opportunities and support programs for startups
          </p>
        </div>

        {/* Filter */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Sector
          </label>
          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          >
            {sectors.map((sector) => (
              <option key={sector} value={sector}>{sector}</option>
            ))}
          </select>
        </div>

        {/* Policy Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredPolicies.map((policy) => (
            <div
              key={policy.id}
              className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200 cursor-pointer"
              onClick={() => setSelectedPolicy(policy)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Building className="w-6 h-6 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 text-lg">
                      {policy.scheme_name}
                    </h3>
                    <p className="text-sm text-gray-600">{policy.authority}</p>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">
                  {policy.sector}
                </span>
              </div>

              <p className="text-gray-700 mb-4 line-clamp-3">
                {policy.description}
              </p>

              <div className="space-y-2 mb-4">
                <p className="text-sm font-semibold text-gray-700">Key Benefits:</p>
                <ul className="space-y-1">
                  {policy.benefits.slice(0, 2).map((benefit, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {policy.deadline && (
                <div className="flex items-center gap-2 text-sm text-orange-600 mb-4">
                  <Calendar className="w-4 h-4" />
                  <span>Deadline: {policy.deadline}</span>
                </div>
              )}
              <button className="w-full py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors font-medium">
                View Details
              </button>
            </div>
          ))}
        </div>

        {/* Policy Details Modal */}
        {selectedPolicy && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      {selectedPolicy.scheme_name}
                    </h2>
                    <p className="text-gray-600">{selectedPolicy.authority}</p>
                  </div>
                  <button
                    onClick={() => setSelectedPolicy(null)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-700">{selectedPolicy.description}</p>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Eligibility Criteria</h3>
                    <ul className="space-y-2">
                      {selectedPolicy.eligibility.map((criterion, index) => (
                        <li key={index} className="flex items-start gap-2 text-gray-700">
                          <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                          <span>{criterion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Benefits</h3>
                    <ul className="space-y-2">
                      {selectedPolicy.benefits.map((benefit, index) => (
                        <li key={index} className="flex items-start gap-2 text-gray-700">
                          <CheckCircle className="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" />
                          <span>{benefit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {selectedPolicy.deadline && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-orange-700">
                        <Calendar className="w-5 h-5" />
                        <p className="font-semibold">Application Deadline: {selectedPolicy.deadline}</p>
                      </div>
                    </div>
                  )}

                  {selectedPolicy.source_url && (
                    <a
                      href={selectedPolicy.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                    >
                      <ExternalLink className="w-5 h-5" />
                      Visit Official Website
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
