'use client';

import { Upload, TrendingUp, Users, FileText } from 'lucide-react';
import Link from 'next/link';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';

export default function FounderPage() {

  const founderActions = [
    {
      title: 'Upload Pitch Deck',
      description: 'Upload your pitch deck for AI-powered analysis and investor matching',
      icon: Upload,
      href: '/founder/upload',
      color: 'bg-blue-500',
    },
    {
      title: 'Find Investors',
      description: 'Discover investors that match your startup profile and funding needs',
      icon: Users,
      href: '/investors',
      color: 'bg-green-500',
    },
    {
      title: 'Market Trends',
      description: 'Explore funding trends and market insights in your industry',
      icon: TrendingUp,
      href: '/trends',
      color: 'bg-purple-500',
    },
    {
      title: 'Policy Information',
      description: 'Learn about government schemes and policies for startups',
      icon: FileText,
      href: '/policies',
      color: 'bg-orange-500',
    },
  ];

  return (
    <ProtectedRoute allowedRoles={['founder']}>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Founder Dashboard
          </h1>
          <p className="text-xl text-gray-600">
            Tools and insights to accelerate your startup journey
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {founderActions.map((action) => {
            const IconComponent = action.icon;
            return (
              <Link
                key={action.title}
                href={action.href}
                className="group"
              >
                <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200">
                  <div className={`${action.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`}>
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {action.title}
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {action.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-12 bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Quick Actions
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                <Upload className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">AI Analysis</h3>
              <p className="text-gray-600 text-sm">
                Get instant AI-powered feedback on your pitch deck
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                <Users className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Investor Matching</h3>
              <p className="text-gray-600 text-sm">
                Find investors who are actively funding startups like yours
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                <TrendingUp className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Market Insights</h3>
              <p className="text-gray-600 text-sm">
                Stay informed about the latest funding trends and opportunities
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
