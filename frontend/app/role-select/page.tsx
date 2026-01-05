'use client';

import { useRouter } from 'next/navigation';
import { Users, Building2, Sparkles } from 'lucide-react';

export default function RoleSelectPage() {
  const router = useRouter();

  const selectRole = (role: 'founder' | 'investor') => {
    // Store role in localStorage
    localStorage.setItem('userRole', role);
    
    // Redirect based on role
    if (role === 'founder') {
      router.push('/founder/upload');
    } else {
      router.push('/investor/thesis');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
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

        <div className="grid md:grid-cols-2 gap-8">
          {/* Founder Card */}
          <button
            onClick={() => selectRole('founder')}
            className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 text-left border-2 border-transparent hover:border-indigo-500"
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
          </button>

          {/* Investor Card */}
          <button
            onClick={() => selectRole('investor')}
            className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 text-left border-2 border-transparent hover:border-purple-500"
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
          </button>
        </div>
      </div>
    </div>
  );
}
