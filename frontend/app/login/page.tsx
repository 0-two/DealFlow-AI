'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Chrome, Users, Building2, Loader } from 'lucide-react';
import { supabase, signInWithGoogle, getUserProfile } from '@/lib/supabase';

type Step = 'role-select' | 'login';
type Role = 'founder' | 'investor';

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('role-select');
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if user is already logged in
  useEffect(() => {
    checkExistingAuth();
  }, []);

  const checkExistingAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.user) {
      // User is logged in, check their profile
      const profile = await getUserProfile(session.user.id);
      
      if (profile) {
        // Check if remember me is still valid
        if (profile.remember_me && profile.remember_me_expires) {
          const expiresAt = new Date(profile.remember_me_expires);
          if (expiresAt > new Date()) {
            // Auto-login
            localStorage.setItem('userRole', profile.role);
            localStorage.setItem('userProfile', JSON.stringify(profile));
            router.push('/chat');
            return;
          }
        }
        
        // Profile exists but remember me expired or not set
        if (!profile.remember_me) {
          // Log them out
          await supabase.auth.signOut();
        }
      }
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
      // Store selected role and remember me preference temporarily
      sessionStorage.setItem('pendingRole', selectedRole);
      sessionStorage.setItem('pendingRememberMe', String(rememberMe));

      await signInWithGoogle();
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google');
      setIsLoading(false);
    }
  };

  const handleBackToRoleSelect = () => {
    setStep('role-select');
    setSelectedRole(null);
  };

  if (step === 'role-select') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
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
                I'm a Founder
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
                I'm an Investor
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

          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
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

          <div className="mt-6 flex items-center">
            <input
              type="checkbox"
              id="rememberMe"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <label htmlFor="rememberMe" className="ml-2 text-sm text-gray-700">
              Remember me for 30 days
            </label>
          </div>

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
