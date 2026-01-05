'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, TrendingUp, Users, Search } from 'lucide-react';
import Link from 'next/link';

export default function InvestorPage() {
  const router = useRouter();

  useEffect(() => {
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'investor') {
      router.push('/role-select');
    }
  }, [router]);

  const investorActions = [
    {
      title: 'Submit Investment Thesis',
      description: 'Define your investment preferences and thesis for better startup matching',
      icon: FileText,
      href: '/investor/thesis',
      color: 'bg-blue-500',
    },
    {
      title: 'Discover Startups',
      description: 'Find startups that match your investment criteria and thesis',
      icon: Search,
      href: '/investors',
      color: 'bg-green-500',
    },
    {
      title: 'Market Trends',
      description: 'Analyze funding trends and market dynamics across sectors',
      icon: TrendingUp,
      href: '/trends',
      color: 'bg-purple-500',
    },
    {
      title: 'Startup Ecosystem',
      description: 'Explore the broader startup ecosystem and policy landscape',
      icon: Users,
      href: '/policies',
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Investor Dashboard
          </h1>
          <p className="text-xl text-gray-600">
            Discover and connect with promising startups in your focus areas
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {investorActions.map((action) => {
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
            Investment Tools
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Thesis Matching</h3>
              <p className="text-gray-600 text-sm">
                Get AI-powered startup recommendations based on your investment thesis
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                <Search className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Smart Discovery</h3>
              <p className="text-gray-600 text-sm">
                Advanced filtering and search to find the perfect investment opportunities
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                <TrendingUp className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Market Analytics</h3>
              <p className="text-gray-600 text-sm">
                Data-driven insights into funding trends and market opportunities
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Recent Activity
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h4 className="font-semibold text-gray-900">No recent activity</h4>
                <p className="text-gray-600 text-sm">Start by submitting your investment thesis</p>
              </div>
              <Link
                href="/investor/thesis"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
