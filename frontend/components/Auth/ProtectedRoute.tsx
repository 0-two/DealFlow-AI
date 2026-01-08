'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Loader } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ('founder' | 'investor')[];
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { session, profile, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      const cached = typeof window !== 'undefined' ? localStorage.getItem('userProfile') : null;
      if ((!session || !profile) && !cached) {
        // Not authenticated and no cached profile, redirect to login
        router.push('/login');
      } else if (profile && allowedRoles && !allowedRoles.includes(profile.role)) {
        // Wrong role, redirect to appropriate page
        router.push('/chat');
      }
    }
  }, [session, profile, loading, allowedRoles, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-lg text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  if (!session || !profile) {
    const cached = typeof window !== 'undefined' ? localStorage.getItem('userProfile') : null;
    if (cached) {
      // Show a lightweight loader while hydrating profile to avoid redirect flicker on refresh
      return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
          <div className="text-center">
            <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
            <p className="text-lg text-gray-700">Restoring your session…</p>
          </div>
        </div>
      );
    }
    return null;
  }

  if (allowedRoles && !allowedRoles.includes(profile.role)) {
    return null;
  }

  return <>{children}</>;
}
