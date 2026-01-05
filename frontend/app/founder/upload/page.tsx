'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import Header from '@/components/Layout/Header';
import { Upload, FileText, Loader, CheckCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PitchDeckUploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [email, setEmail] = useState('');
  const [website, setWebsite] = useState('');
  const [uploadMode, setUploadMode] = useState<'pitch' | 'manual'>('pitch');

  // Manual form fields
  const [manualData, setManualData] = useState({
    startup_name: '',
    founder_name: '',
    sector: '',
    stage: '',
    location: '',
    funding_amount: '',
    description: '',
    problem_statement: '',
    solution: '',
    traction: '',
    team_size: '',
    revenue: '',
  });

  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await axios.post(
        `${API_URL}/api/pitch-deck/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      return response.data;
    },
  });

  const manualSubmitMutation = useMutation({
    mutationFn: async (data: any) => {
      const formData = new FormData();
      Object.keys(data).forEach((key) => {
        formData.append(key, data[key]);
      });
      formData.append('user_context', JSON.stringify({ role: 'founder' }));
      
      const response = await axios.post(
        `${API_URL}/api/pitch-deck/manual-submit`,
        formData
      );
      return response.data;
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handlePitchDeckUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('user_context', JSON.stringify({ role: 'founder' }));
    formData.append('contact_email', email);
    formData.append('website', website);

    uploadMutation.mutate(formData);
  };

  const handleManualSubmit = async () => {
    const data = {
      ...manualData,
      contact_email: email,
      website: website,
    };
    manualSubmitMutation.mutate(data);
  };

  const result = uploadMutation.data || manualSubmitMutation.data;
  const isLoading = uploadMutation.isPending || manualSubmitMutation.isPending;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header selectedLanguage="en" onLanguageChange={() => {}} />

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Upload Your Pitch Deck
          </h1>
          <p className="text-gray-600">
            Let AI find the perfect investors for your startup
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="bg-white rounded-xl shadow-md p-2 mb-8 inline-flex">
          <button
            onClick={() => setUploadMode('pitch')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              uploadMode === 'pitch'
                ? 'bg-indigo-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Upload Pitch Deck
          </button>
          <button
            onClick={() => setUploadMode('manual')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              uploadMode === 'manual'
                ? 'bg-indigo-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Enter Details Manually
          </button>
        </div>

        {!result ? (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            {uploadMode === 'pitch' ? (
              /* Pitch Deck Upload */
              <div>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center mb-6">
                  {!selectedFile ? (
                    <div>
                      <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-600 mb-4">
                        Drop your pitch deck here or click to browse
                      </p>
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileSelect}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg cursor-pointer hover:bg-indigo-700 transition-colors"
                      >
                        Choose PDF File
                      </label>
                    </div>
                  ) : (
                    <div>
                      <FileText className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
                      <p className="text-gray-900 font-medium mb-2">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-gray-500 mb-4">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>

                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="founder@startup.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Website (Optional)
                    </label>
                    <input
                      type="url"
                      value={website}
                      onChange={(e) => setWebsite(e.target.value)}
                      placeholder="https://yourstartup.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                    />
                  </div>
                </div>

                <button
                  onClick={handlePitchDeckUpload}
                  disabled={!selectedFile || isLoading}
                  className="w-full py-4 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Upload & Find Investors
                    </>
                  )}
                </button>
              </div>
            ) : (
              /* Manual Entry Form */
              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Startup Name *
                    </label>
                    <input
                      type="text"
                      value={manualData.startup_name}
                      onChange={(e) => setManualData({ ...manualData, startup_name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Founder Name *
                    </label>
                    <input
                      type="text"
                      value={manualData.founder_name}
                      onChange={(e) => setManualData({ ...manualData, founder_name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sector *
                    </label>
                    <select
                      value={manualData.sector}
                      onChange={(e) => setManualData({ ...manualData, sector: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    >
                      <option value="">Select Sector</option>
                      <option value="Fintech">Fintech</option>
                      <option value="Edtech">Edtech</option>
                      <option value="Healthtech">Healthtech</option>
                      <option value="E-commerce">E-commerce</option>
                      <option value="SaaS">SaaS</option>
                      <option value="AI/ML">AI/ML</option>
                      <option value="Agritech">Agritech</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Stage *
                    </label>
                    <select
                      value={manualData.stage}
                      onChange={(e) => setManualData({ ...manualData, stage: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    >
                      <option value="">Select Stage</option>
                      <option value="Pre-Seed">Pre-Seed</option>
                      <option value="Seed">Seed</option>
                      <option value="Series A">Series A</option>
                      <option value="Series B">Series B</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location *
                    </label>
                    <input
                      type="text"
                      value={manualData.location}
                      onChange={(e) => setManualData({ ...manualData, location: e.target.value })}
                      placeholder="Bangalore"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Funding Amount (₹ Crores) *
                    </label>
                    <input
                      type="number"
                      value={manualData.funding_amount}
                      onChange={(e) => setManualData({ ...manualData, funding_amount: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <textarea
                    value={manualData.description}
                    onChange={(e) => setManualData({ ...manualData, description: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Problem Statement
                  </label>
                  <textarea
                    value={manualData.problem_statement}
                    onChange={(e) => setManualData({ ...manualData, problem_statement: e.target.value })}
                    rows={2}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Solution
                  </label>
                  <textarea
                    value={manualData.solution}
                    onChange={(e) => setManualData({ ...manualData, solution: e.target.value })}
                    rows={2}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contact Email *
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Website
                    </label>
                    <input
                      type="url"
                      value={website}
                      onChange={(e) => setWebsite(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                  </div>
                </div>

                <button
                  onClick={handleManualSubmit}
                  disabled={isLoading || !manualData.startup_name || !email}
                  className="w-full py-4 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Submit & Find Investors'
                  )}
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Results Display */
          <div className="space-y-6">
            {/* Success Message */}
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h2 className="text-xl font-bold text-green-900">
                  Success! Found {result.matched_investors.length} Matching Investors
                </h2>
              </div>
              <p className="text-green-700">{result.message}</p>
            </div>

            {/* Startup Profile */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Your Startup Profile
              </h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium">{result.startup_profile.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Sector:</span>
                  <span className="ml-2 font-medium">{result.startup_profile.sector}</span>
                </div>
                <div>
                  <span className="text-gray-600">Stage:</span>
                  <span className="ml-2 font-medium">{result.startup_profile.stage}</span>
                </div>
                <div>
                  <span className="text-gray-600">Location:</span>
                  <span className="ml-2 font-medium">{result.startup_profile.location}</span>
                </div>
                <div className="md:col-span-2">
                  <span className="text-gray-600">Funding Need:</span>
                  <span className="ml-2 font-medium">₹{result.startup_profile.funding_amount} Cr</span>
                </div>
              </div>
            </div>

            {/* Matched Investors */}
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Recommended Investors
              </h3>
              <div className="space-y-4">
                {result.matched_investors.map((match: any, index: number) => (
                  <div
                    key={index}
                    className="bg-white rounded-xl shadow-md p-6 border border-gray-200"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-xl font-bold text-gray-900">
                          {match.profile.name}
                        </h4>
                        <p className="text-sm text-indigo-600">{match.profile.type}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-indigo-600">
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
                        <span className="text-gray-600">Focus Areas:</span>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {match.profile.focus_areas?.map((area: string, i: number) => (
                            <span
                              key={i}
                              className="px-2 py-1 bg-indigo-50 text-indigo-700 text-xs rounded-full"
                            >
                              {area}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-600">Ticket Size:</span>
                        <span className="ml-2 font-medium">
                          ₹{match.profile.ticket_size_min}-{match.profile.ticket_size_max} Cr
                        </span>
                      </div>
                    </div>

                    {match.profile.portfolio && match.profile.portfolio.length > 0 && (
                      <div className="text-sm">
                        <span className="text-gray-600">Portfolio:</span>
                        <span className="ml-2">{match.profile.portfolio.join(', ')}</span>
                      </div>
                    )}

                    {(match.profile.contact_email || match.profile.website) && (
                      <div className="mt-4 flex gap-2">
                        {match.profile.contact_email && (
                          <a
                            href={`mailto:${match.profile.contact_email}`}
                            className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm font-medium"
                          >
                            Contact
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
                manualSubmitMutation.reset();
                setSelectedFile(null);
                setManualData({
                  startup_name: '',
                  founder_name: '',
                  sector: '',
                  stage: '',
                  location: '',
                  funding_amount: '',
                  description: '',
                  problem_statement: '',
                  solution: '',
                  traction: '',
                  team_size: '',
                  revenue: '',
                });
              }}
              className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
            >
              Upload Another
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
