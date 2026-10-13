'use client';

import { useState, useEffect } from 'react';
import { Chrome, Users, Building2, Loader, AlertTriangle } from 'lucide-react';
import { signInWithGoogle, isSupabaseConfigured } from '@/lib/supabase';

type Step = 'role-select' | 'login';
type Role = 'founder' | 'investor';

export default function LoginPage() {
  const [step, setStep] = useState<Step>('role-select');
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check if user is already logged in or has pending role
  useEffect(() => {
    initializePage();
  }, []);

  const initializePage = async () => {
    try {
      // If Supabase is not configured, stop initializing
      if (!isSupabaseConfigured) {
        setIsInitializing(false);
        return;
      }

      // Check for pending role from role-select page
      const pendingRole = localStorage.getItem('pendingRole') as Role | null;
      
      if (pendingRole) {
        setSelectedRole(pendingRole);
        setStep('login');
        // Also set in sessionStorage for OAuth callback
        sessionStorage.setItem('pendingRole', pendingRole);
      }

      // No auto-login; require explicit sign in every visit
    } catch (error) {
      console.error('Error initializing login page:', error);
    } finally {
      setIsInitializing(false);
    }
  };

  const handleRoleSelect = (role: Role) => {
    setSelectedRole(role);
    setStep('login');
  };

  const handleGoogleSignIn = async () => {
    if (!selectedRole) return;

    setIsLoading(true);
    setError(null);

    try {
      // Store selected role in BOTH sessionStorage and localStorage
      // This provides a fallback in case sessionStorage is cleared during OAuth redirect
      sessionStorage.setItem('pendingRole', selectedRole);
      localStorage.setItem('pendingRole', selectedRole);

      console.log('Starting Google sign in with role:', selectedRole);

      await signInWithGoogle();
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google');
      setIsLoading(false);
    }
  };

  const handleBackToRoleSelect = () => {
    setStep('role-select');
    setSelectedRole(null);
    // Clear pending role
    localStorage.removeItem('pendingRole');
    sessionStorage.removeItem('pendingRole');
  };

  // Show loading while initializing
  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-lg text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  if (step === 'role-select') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
          {!isSupabaseConfigured && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-amber-800">Authentication Not Configured</h3>
                <p className="text-sm text-amber-700 mt-1">
                  Supabase environment variables are missing. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file.
                </p>
              </div>
            </div>
          )}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Welcome to DealFlow AI
            </h1>
            <p className="text-xl text-gray-600">
              Choose your role to get started
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Founder Card */}
            <button
              onClick={() => handleRoleSelect('founder')}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 text-left border-2 border-transparent hover:border-indigo-500"
            >
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6">
                <Users className="w-8 h-8 text-indigo-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                I&apos;m a Founder
              </h2>
              <p className="text-gray-600 mb-6">
                Upload your pitch deck, discover investors, and get AI-powered funding insights
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2 text-indigo-600">✓</span> Find matching investors
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2 text-indigo-600">✓</span> AI-powered recommendations
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2 text-indigo-600">✓</span> Multilingual support
                </li>
              </ul>
            </button>

            {/* Investor Card */}
            <button
              onClick={() => handleRoleSelect('investor')}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 text-left border-2 border-transparent hover:border-purple-500"
            >
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-6">
                <Building2 className="w-8 h-8 text-purple-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                I&apos;m an Investor
              </h2>
              <p className="text-gray-600 mb-6">
                Discover promising startups, analyze trends, and find investment opportunities
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2 text-purple-600">✓</span> Browse startup pipeline
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2 text-purple-600">✓</span> Smart matching algorithm
                </li>
                <li className="flex items-center text-sm text-gray-700">
                  <span className="mr-2 text-purple-600">✓</span> Market insights
                </li>
              </ul>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className={`w-16 h-16 ${selectedRole === 'founder' ? 'bg-indigo-100' : 'bg-purple-100'} rounded-full flex items-center justify-center mx-auto mb-4`}>
              {selectedRole === 'founder' ? (
                <Users className={`w-8 h-8 text-indigo-600`} />
              ) : (
                <Building2 className={`w-8 h-8 text-purple-600`} />
              )}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Sign in as {selectedRole === 'founder' ? 'Founder' : 'Investor'}
            </h2>
            <p className="text-gray-600">
              Use your Google account to continue
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {!isSupabaseConfigured && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-amber-700">
                  Authentication is not configured. Please set up Supabase environment variables.
                </p>
              </div>
            </div>
          )}

          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading || !isSupabaseConfigured}
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-white border-2 border-gray-300 rounded-xl font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {isLoading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <Chrome className="w-5 h-5" />
                Continue with Google
              </>
            )}
          </button>

          {/* Remember-me removed: login required every visit */}

          <button
            onClick={handleBackToRoleSelect}
            className="mt-6 w-full text-center text-sm text-gray-600 hover:text-gray-900"
          >
            ← Back to role selection
          </button>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              By continuing, you agree to our Terms of Service and Privacy Policy.
              Your account will be locked to the selected role.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
