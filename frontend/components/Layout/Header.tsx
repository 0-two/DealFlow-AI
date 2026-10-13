'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LanguageCode } from '@/lib/types';
import { Menu, X, Sparkles, LogOut } from 'lucide-react';
import { useTranslationContext } from '@/contexts/TranslationContext';
import { useAuth } from '@/contexts/AuthContext';

interface Props {
  selectedLanguage?: LanguageCode; // deprecated
  onLanguageChange?: (lang: LanguageCode) => void; // deprecated
}

export default function Header(_props: Props) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { profile, switchRole } = useAuth();
  const { t } = useTranslationContext();

  const userRole = profile?.role;

  // Navigation items based on role
  const getNavItems = () => {
    const commonItems = [
      { name: t('nav.ai_chat') || 'Chat', path: '/chat' },
    ];

    const roleSpecificItems: { name: string; path: string }[] = [];
    
    if (userRole === 'founder') {
      roleSpecificItems.push(
        { name: 'Upload Pitch', path: '/founder/upload' },
        { name: 'Investors', path: '/investors' },
        { name: 'Policies', path: '/policies' },
      );
    } else if (userRole === 'investor') {
      roleSpecificItems.push(
        { name: 'My Thesis', path: '/investor/thesis' },
        { name: 'Startups', path: '/startups' },
        { name: 'News', path: '/news' },
      );
    }

    return [...roleSpecificItems, ...commonItems];
  };

  const navItems = getNavItems();

  const handleSwitchRole = async () => {
    try {
      await switchRole();
    } catch (error) {
      console.error('Switch role error:', error);
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
              DealFlow AI
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

          {/* Right side */}
          <div className="hidden md:flex items-center gap-3">
            {/* Role Badge & Switch Role */}
            {userRole && (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full font-medium">
                  {userRole === 'founder' ? '👤 Founder' : '💼 Investor'}
                </span>
                <button
                  onClick={handleSwitchRole}
                  className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
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

            {/* Mobile role & switch remains below */}

            {/* Mobile Role & Switch Role */}
            {userRole && (
              <div className="flex items-center justify-between px-4 py-2 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">
                  {userRole === 'founder' ? '👤 Founder Mode' : '💼 Investor Mode'}
                </span>
                <button
                  onClick={handleSwitchRole}
                  className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
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
