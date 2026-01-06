'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Loader } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { session, profile, loading } = useAuth();
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    // Set a timeout to prevent infinite loading
    const timeoutId = setTimeout(() => {
      if (loading) {
        setTimedOut(true);
        // Redirect to login if still loading after timeout
        router.push('/login');
      }
    }, 5000);

    return () => clearTimeout(timeoutId);
  }, [loading, router]);

  useEffect(() => {
    if (!loading && !timedOut) {
      if (session && profile) {
        // User is authenticated, redirect to chat
        router.push('/chat');
      } else {
        // Not authenticated, redirect to login
        router.push('/login');
      }
    }
  }, [session, profile, loading, timedOut, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">
        <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
        <p className="text-lg text-gray-700">Loading...</p>
      </div>
    </div>
  );
}
