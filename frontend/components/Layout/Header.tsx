'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LanguageCode, LANGUAGES } from '@/lib/types';
import { Menu, X, Sparkles, LogOut, Loader, Globe } from 'lucide-react';
import { useTranslationContext } from '@/contexts/TranslationContext';
import { useAuth } from '@/contexts/AuthContext';

interface Props {
  selectedLanguage?: LanguageCode;
  onLanguageChange?: (lang: LanguageCode) => void;
}

export default function Header({ selectedLanguage, onLanguageChange }: Props) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { session, profile, signOut: authSignOut } = useAuth();
  const { language, changeLanguage, t, isTranslating } = useTranslationContext();
  
  // Use context language if no prop provided
  const currentLang = selectedLanguage || language;

  const userRole = profile?.role;

  // Navigation items based on role
  const getNavItems = () => {
    const commonItems = [
      { name: t('nav.ai_chat') || 'Chat', path: '/chat' },
      { name: 'Trends', path: '/trends' },
      { name: 'Policies', path: '/policies' },
    ];

    const roleSpecificItems = [];
    
    if (userRole === 'founder') {
      roleSpecificItems.push(
        { name: 'Upload Pitch', path: '/founder/upload' },
        { name: 'Investors', path: '/investors' }
      );
    } else if (userRole === 'investor') {
      roleSpecificItems.push(
        { name: 'My Thesis', path: '/investor/thesis' },
        { name: 'Startups', path: '/startups' }
      );
    }

    return [...roleSpecificItems, ...commonItems];
  };

  const navItems = getNavItems();

  const handleLogout = async () => {
    try {
      await authSignOut();
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleLanguageChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLang = e.target.value as LanguageCode;
    
    // Call context handler
    await changeLanguage(newLang);
    
    // Also call prop handler if provided
    if (onLanguageChange) {
      onLanguageChange(newLang);
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-900 hidden sm:block">
              Funding Intelligence
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Right side - Language & Logout */}
          <div className="hidden md:flex items-center gap-3">
            {/* Translation Loading Indicator */}
            {isTranslating && (
              <Loader className="w-4 h-4 animate-spin text-indigo-600" />
            )}
            
            {/* Language Selector */}
            <Globe className="w-5 h-5 text-gray-500" />
            <select
              value={currentLang}
              onChange={handleLanguageChange}
              disabled={isTranslating}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm disabled:opacity-50"
            >
              {Object.entries(LANGUAGES).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>

            {/* Role Badge & Logout */}
            {userRole && (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full font-medium">
                  {userRole === 'founder' ? '👤 Founder' : '💼 Investor'}
                </span>
                <button
                  onClick={handleLogout}
                  className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Switch Role"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <nav className="flex flex-col gap-2 mb-4">
              {navItems.map((item) => {
                const isActive = pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    href={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </nav>

            {/* Mobile Language Selector */}
            <div className="flex items-center gap-2 mb-3">
              {isTranslating && (
                <Loader className="w-4 h-4 animate-spin text-indigo-600" />
              )}
              <select
                value={currentLang}
                onChange={handleLanguageChange}
                disabled={isTranslating}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-50"
              >
                {Object.entries(LANGUAGES).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            {/* Mobile Role & Logout */}
            {userRole && (
              <div className="flex items-center justify-between px-4 py-2 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">
                  {userRole === 'founder' ? '👤 Founder Mode' : '💼 Investor Mode'}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  Switch Role
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
