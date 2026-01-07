'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import Header from '@/components/Layout/Header';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import { Building2, Loader, CheckCircle, FileText } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function InvestorThesisPage() {
  const [formData, setFormData] = useState({
    investor_name: '',
    investment_thesis: '',
    focus_sectors: '',
    stages: '',
    geographies: '',
    ticket_size_min: '',
    ticket_size_max: '',
    investment_criteria: '',
    portfolio: '',
    contact_email: '',
    website: '',
  });

  const uploadMutation = useMutation({
    mutationFn: async (data: any) => {
      const formDataObj = new FormData();
      Object.keys(data).forEach((key) => {
        formDataObj.append(key, data[key]);
      });
      formDataObj.append('user_context', JSON.stringify({ role: 'investor' }));

      const response = await axios.post(
        `${API_URL}/api/investor-thesis/upload-thesis`,
        formDataObj
      );
      return response.data;
    },
  });

  const handleSubmit = () => {
    uploadMutation.mutate(formData);
  };

  const result = uploadMutation.data;

  return (
    <ProtectedRoute allowedRoles={['investor']}>
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
      <Header selectedLanguage="en" onLanguageChange={() => {}} />

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Define Your Investment Thesis
          </h1>
          <p className="text-gray-600">
            Let AI find startups that align with your investment strategy
          </p>
        </div>

        {!result ? (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Investor/Firm Name *
                </label>
                <input
                  type="text"
                  value={formData.investor_name}
                  onChange={(e) => setFormData({ ...formData, investor_name: e.target.value })}
                  placeholder="Accel Partners India"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Investment Thesis *
                </label>
                <textarea
                  value={formData.investment_thesis}
                  onChange={(e) => setFormData({ ...formData, investment_thesis: e.target.value })}
                  placeholder="We invest in early-stage technology companies solving large problems in India..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                  required
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Focus Sectors * (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.focus_sectors}
                    onChange={(e) => setFormData({ ...formData, focus_sectors: e.target.value })}
                    placeholder="Fintech, SaaS, E-commerce"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Stages * (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.stages}
                    onChange={(e) => setFormData({ ...formData, stages: e.target.value })}
                    placeholder="Seed, Series A, Series B"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Geographies * (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.geographies}
                    onChange={(e) => setFormData({ ...formData, geographies: e.target.value })}
                    placeholder="Bangalore, Mumbai, Delhi NCR"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Portfolio Companies (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.portfolio}
                    onChange={(e) => setFormData({ ...formData, portfolio: e.target.value })}
                    placeholder="Swiggy, Urban Company, Freshworks"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Ticket Size (₹ Crores) *
                  </label>
                  <input
                    type="number"
                    value={formData.ticket_size_min}
                    onChange={(e) => setFormData({ ...formData, ticket_size_min: e.target.value })}
                    placeholder="5"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Ticket Size (₹ Crores) *
                  </label>
                  <input
                    type="number"
                    value={formData.ticket_size_max}
                    onChange={(e) => setFormData({ ...formData, ticket_size_max: e.target.value })}
                    placeholder="50"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Investment Criteria
                </label>
                <textarea
                  value={formData.investment_criteria}
                  onChange={(e) => setFormData({ ...formData, investment_criteria: e.target.value })}
                  placeholder="Strong founding team, proven traction, scalable business model..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Email *
                  </label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    placeholder="invest@firm.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Website
                  </label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    placeholder="https://firm.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                  />
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={uploadMutation.isPending || !formData.investor_name || !formData.contact_email}
                className="w-full py-4 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {uploadMutation.isPending ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Finding Startups...
                  </>
                ) : (
                  <>
                    <Building2 className="w-5 h-5" />
                    Submit & Find Startups
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Results */
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h2 className="text-xl font-bold text-green-900">
                  Found {result.matched_startups.length} Matching Startups
                </h2>
              </div>
              <p className="text-green-700">{result.message}</p>
            </div>

            {/* Investor Profile */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Your Investment Profile
              </h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">Focus Sectors:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {result.investor_profile.focus_sectors.map((sector: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-purple-50 text-purple-700 rounded-full">
                        {sector}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-gray-600">Stages:</span>
                  <span className="ml-2">{result.investor_profile.stages.join(', ')}</span>
                </div>
                <div>
                  <span className="text-gray-600">Ticket Size:</span>
                  <span className="ml-2 font-medium">{result.investor_profile.ticket_size}</span>
                </div>
              </div>
            </div>

            {/* Matched Startups */}
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Recommended Startups
              </h3>
              <div className="space-y-4">
                {result.matched_startups.map((match: any, index: number) => (
                  <div
                    key={index}
                    className="bg-white rounded-xl shadow-md p-6 border border-gray-200"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-xl font-bold text-gray-900">
                          {match.profile.startup_name}
                        </h4>
                        <p className="text-sm text-purple-600">
                          {match.profile.sector} • {match.profile.stage}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-purple-600">
                          {(match.match_score * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500">Match Score</div>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm font-semibold text-gray-700 mb-1">
                        Why this is a good match:
                      </p>
                      <p className="text-gray-600">{match.reasoning}</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-gray-600">Location:</span>
                        <span className="ml-2 font-medium">{match.profile.location}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Funding Need:</span>
                        <span className="ml-2 font-medium">₹{match.profile.funding_amount} Cr</span>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm text-gray-700">
                        {match.profile.description}
                      </p>
                    </div>

                    {match.profile.traction && (
                      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-600 mb-1">Traction:</p>
                        <p className="text-sm text-gray-800">{match.profile.traction}</p>
                      </div>
                    )}

                    {(match.profile.contact_email || match.profile.website) && (
                      <div className="flex gap-2">
                        {match.profile.contact_email && (
                          <a
                            href={`mailto:${match.profile.contact_email}`}
                            className="px-4 py-2 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors text-sm font-medium"
                          >
                            Contact Founder
                          </a>
                        )}
                        {match.profile.website && (
                          <a
                            href={match.profile.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                          >
                            Visit Website
                          </a>
                        )}
                      </div>
                    )}

                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <FileText className="w-4 h-4" />
                        <span>Source: {match.source.collection} Database</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => {
                uploadMutation.reset();
                setFormData({
                  investor_name: '',
                  investment_thesis: '',
                  focus_sectors: '',
                  stages: '',
                  geographies: '',
                  ticket_size_min: '',
                  ticket_size_max: '',
                  investment_criteria: '',
                  portfolio: '',
                  contact_email: '',
                  website: '',
                });
              }}
              className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
            >
              Submit Another Thesis
            </button>
          </div>
        )}
      </main>
    </div>
    </ProtectedRoute>
  );
}
