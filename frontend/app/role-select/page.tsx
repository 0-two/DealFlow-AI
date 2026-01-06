'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Users, Building2, Sparkles, Loader } from 'lucide-react';

export default function RoleSelectPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectRole = async (role: 'founder' | 'investor') => {
    setIsLoading(true);
    setError(null);

    try {
      // Store role selection
      localStorage.setItem('pendingRole', role);
      sessionStorage.setItem('pendingRole', role);
      
      // Always redirect to login - let login page handle auth state
      router.push('/login');
    } catch (err) {
      console.error('Error selecting role:', err);
      setError('An error occurred. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Simple Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-900">Funding Intelligence</span>
          </div>
        </div>
      </header>
      
      <div className="flex items-center justify-center p-4 pt-12">
        <div className="max-w-4xl w-full">
          <div className="text-center mb-12">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Welcome to Funding Intelligence
            </h1>
            <p className="text-xl text-gray-600">
              Find your perfect match in the startup ecosystem
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-8">
            {/* Founder Card */}
            <button
              onClick={() => selectRole('founder')}
              disabled={isLoading}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 text-left border-2 border-transparent hover:border-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6">
                <Users className="w-8 h-8 text-indigo-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                I'm a Founder
              </h2>
              <p className="text-gray-600 mb-6">
                Upload your pitch deck or startup details to find investors who match your vision.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> Upload pitch decks
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> AI-powered investor matching
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> Get personalized recommendations
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> Multilingual support
                </li>
              </ul>
              {isLoading && (
                <Loader className="w-5 h-5 animate-spin mt-4 text-indigo-600" />
              )}
            </button>

            {/* Investor Card */}
            <button
              onClick={() => selectRole('investor')}
              disabled={isLoading}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 text-left border-2 border-transparent hover:border-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-6">
                <Building2 className="w-8 h-8 text-purple-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                I'm an Investor
              </h2>
              <p className="text-gray-600 mb-6">
                Share your investment thesis and discover startups that align with your portfolio.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> Define investment thesis
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> AI-powered startup matching
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> Discover emerging opportunities
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> Multilingual support
                </li>
              </ul>
              {isLoading && (
                <Loader className="w-5 h-5 animate-spin mt-4 text-purple-600" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
