'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Loader } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { session, profile, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (session && profile) {
        // User is authenticated, redirect to chat
        router.push('/chat');
      } else {
        // Not authenticated, redirect to login
        router.push('/login');
      }
    }
  }, [session, profile, loading, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">
        <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
        <p className="text-lg text-gray-700">Loading...</p>
      </div>
    </div>
  );
}
