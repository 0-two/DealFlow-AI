'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader } from 'lucide-react';
import { supabase, getUserProfile, createUserProfile } from '@/lib/supabase';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [status, setStatus] = useState('Processing authentication...');

  useEffect(() => {
    handleAuthCallback();
  }, []);

  const handleAuthCallback = async () => {
    try {
      // Get the session from the URL hash
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError) {
        throw sessionError;
      }

      if (!session?.user) {
        throw new Error('No user session found');
      }

      setStatus('Setting up your account...');

      // Get pending role and remember me from session storage
      const pendingRole = sessionStorage.getItem('pendingRole') as 'founder' | 'investor' | null;
      const pendingRememberMe = sessionStorage.getItem('pendingRememberMe') === 'true';

      if (!pendingRole) {
        throw new Error('No role selected. Please try again.');
      }

      // Check if user profile already exists
      let profile = await getUserProfile(session.user.id);

      if (profile) {
        // User already has a profile
        // Check if they're trying to sign in with a different role
        if (profile.role !== pendingRole) {
          setStatus('Error: Account already registered with different role');
          await supabase.auth.signOut();
          
          setTimeout(() => {
            router.push('/login?error=role_mismatch');
          }, 2000);
          return;
        }

        // Update remember me if needed
        if (pendingRememberMe !== profile.remember_me) {
          const rememberMeExpires = pendingRememberMe
            ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
            : null;

          await supabase
            .from('user_profiles')
            .update({
              remember_me: pendingRememberMe,
              remember_me_expires: rememberMeExpires,
            })
            .eq('id', session.user.id);

          profile.remember_me = pendingRememberMe;
          profile.remember_me_expires = rememberMeExpires || undefined;
        }
      } else {
        // Create new profile
        setStatus('Creating your profile...');
        
        profile = await createUserProfile(
          session.user.id,
          session.user.email!,
          pendingRole,
          session.user.user_metadata?.full_name || session.user.email?.split('@')[0],
          pendingRememberMe
        );

        if (!profile) {
          // Profile creation failed, but user is authenticated
          // Create a basic profile object for local use
          console.warn('Profile creation returned null, using fallback');
          profile = {
            id: session.user.id,
            email: session.user.email!,
            role: pendingRole,
            full_name: session.user.user_metadata?.full_name || session.user.email?.split('@')[0],
            created_at: new Date().toISOString(),
            remember_me: pendingRememberMe,
            remember_me_expires: pendingRememberMe 
              ? new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() 
              : undefined,
          };
        }
      }

      // Store user info in localStorage
      localStorage.setItem('userRole', profile.role);
      localStorage.setItem('userProfile', JSON.stringify(profile));

      // Clear session storage
      sessionStorage.removeItem('pendingRole');
      sessionStorage.removeItem('pendingRememberMe');

      setStatus('Success! Redirecting...');

      // Redirect to chat
      setTimeout(() => {
        router.push('/chat');
      }, 1000);

    } catch (error: any) {
      console.error('Auth callback error:', error);
      setStatus(`Error: ${error.message}`);
      
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">
        <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
        <p className="text-lg text-gray-700">{status}</p>
      </div>
    </div>
  );
}
