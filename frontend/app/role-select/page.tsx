'use client';

import { useRouter } from 'next/navigation';
import { Users, Building2, Sparkles, Loader } from 'lucide-react';
import { useTranslationContext } from '@/contexts/TranslationContext';
import Header from '@/components/Layout/Header';

export default function RoleSelectPage() {
  const router = useRouter();
  const { t, isTranslating } = useTranslationContext();

  const selectRole = (role: 'founder' | 'investor') => {
    localStorage.setItem('userRole', role);
    // Redirect to chat page with role parameter
    router.push(`/chat?role=${role}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <div className="flex items-center justify-center p-4 pt-12">
        <div className="max-w-4xl w-full">
          <div className="text-center mb-12">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              {isTranslating ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader className="w-6 h-6 animate-spin" />
                  {t('role.welcome')}
                </span>
              ) : (
                t('role.welcome')
              )}
            </h1>
            <p className="text-xl text-gray-600">
              {t('role.subtitle')}
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
                {t('role.founder')}
              </h2>
              <p className="text-gray-600 mb-6">
                {t('role.founder_desc')}
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.upload_pitch')}
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.ai_investor_match')}
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.personalized_recs')}
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.multilingual')}
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
                {t('role.investor')}
              </h2>
              <p className="text-gray-600 mb-6">
                {t('role.investor_desc')}
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.define_thesis')}
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.ai_startup_match')}
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.discover_opps')}
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2">✓</span> {t('role.multilingual')}
                </li>
              </ul>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
