'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader } from 'lucide-react';
import { supabase, getUserProfile, createUserProfile } from '@/lib/supabase';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [status, setStatus] = useState('Processing authentication...');
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  const addDebug = (msg: string) => {
    console.log(msg);
    setDebugInfo(prev => [...prev, msg]);
  };

  useEffect(() => {
    // Add a timeout to prevent infinite stuck state
    const timeout = setTimeout(() => {
      console.error('⏱️ Auth callback timeout - redirecting to login');
      addDebug('❌ Timeout after 30 seconds');
      router.push('/login?error=timeout');
    }, 30000); // 30 second timeout

    handleAuthCallback().finally(() => {
      clearTimeout(timeout);
    });

    return () => clearTimeout(timeout);
  }, []);

  const handleAuthCallback = async () => {
    try {
      addDebug('🔐 Auth callback started');
      setStatus('Getting your session...');
      
      // Get the session from the URL hash
      const { data: { session }, error: sessionError } = await Promise.race([
        supabase.auth.getSession(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Session fetch timeout')), 10000) // 10s for session
        )
      ]) as any;

      addDebug(`📝 Session: ${session ? '✅ Found' : '❌ Not found'}`);
      if (session?.user) {
        addDebug(`👤 User: ${session.user.email}`);
      }

      if (sessionError) {
        addDebug(`❌ Session error: ${sessionError.message}`);
        throw sessionError;
      }

      if (!session?.user) {
        addDebug('❌ No user in session');
        throw new Error('No user session found');
      }

      setStatus('Checking your role...');

      // Get pending role from storage
      const pendingRole = sessionStorage.getItem('pendingRole') as 'founder' | 'investor' | null;

      addDebug(`🎭 Role (session): ${pendingRole || 'none'}`);

      if (!pendingRole) {
        // Fallback: check localStorage for pending role
        const localRole = localStorage.getItem('pendingRole') as 'founder' | 'investor' | null;
        addDebug(`🎭 Role (local): ${localRole || 'none'}`);
        
        if (localRole) {
          addDebug(`✅ Using localStorage role: ${localRole}`);
          await processUserWithRole(session, localRole);
          return;
        }
        addDebug('❌ No role found');
        throw new Error('No role selected. Please try again.');
      }

      addDebug(`✅ Processing with role: ${pendingRole}`);
      await processUserWithRole(session, pendingRole);

    } catch (error: any) {
      console.error('💥 Auth callback error:', error);
      addDebug(`💥 Error: ${error.message}`);
      setStatus(`Error: ${error.message}`);
      
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    }
  };

  const processUserWithRole = async (
    session: any, 
    role: 'founder' | 'investor'
  ) => {
    try {
      addDebug('🔍 Checking profile...');
      setStatus('Setting up your account...');
      
      // Try to get profile with shorter timeout - if it fails, just use fallback
      let profile = null;
      try {
        profile = await Promise.race([
          getUserProfile(session.user.id),
          new Promise<null>((_, reject) => 
            setTimeout(() => reject(new Error('timeout')), 3000) // 3 second timeout
          )
        ]);
        
        if (profile) {
          addDebug(`📊 Profile found: ${profile.role}`);
          
          // Check role mismatch
          if (profile.role !== role) {
            addDebug(`❌ Role mismatch: ${profile.role} vs ${role}`);
            setStatus('Error: Account already registered with different role');
            await supabase.auth.signOut();
            
            setTimeout(() => {
              router.push('/login?error=role_mismatch');
            }, 2000);
            return;
          }
        }
      } catch (err: any) {
        addDebug(`⚠️ Profile fetch failed: ${err.message}`);
        // Continue with fallback - don't throw
      }

      // If no profile found, try to create one (but don't wait long)
      if (!profile) {
        addDebug('➕ Creating profile...');
        
        try {
          profile = await Promise.race([
            createUserProfile(
              session.user.id,
              session.user.email!,
              role,
              session.user.user_metadata?.full_name || session.user.email?.split('@')[0]
            ),
            new Promise<null>((_, reject) => 
              setTimeout(() => reject(new Error('timeout')), 3000) // 3 second timeout
            )
          ]);
          
          if (profile) {
            addDebug('✅ Profile created in DB');
          }
        } catch (err: any) {
          addDebug(`⚠️ Profile creation failed: ${err.message}`);
          // Continue with fallback - don't throw
        }
      }

      // Always use fallback if profile is still null
      if (!profile) {
        addDebug('✅ Using local profile (DB unavailable)');
        profile = {
          id: session.user.id,
          email: session.user.email!,
          role: role,
          full_name: session.user.user_metadata?.full_name || session.user.email?.split('@')[0],
          created_at: new Date().toISOString(),
        };
      }

      addDebug('💾 Saving to localStorage...');
      localStorage.setItem('userRole', profile.role);
      localStorage.setItem('userProfile', JSON.stringify(profile));

      addDebug('🧹 Clearing temp storage...');
      sessionStorage.removeItem('pendingRole');
      localStorage.removeItem('pendingRole');
      // Removed remember-me storage cleanup

      addDebug('✅ Success! Redirecting...');
      setStatus('Success! Redirecting to chat...');

      setTimeout(() => {
        addDebug('🚀 Navigating to /chat');
        router.push('/chat');
      }, 800);

    } catch (error: any) {
      console.error('💥 Process user error:', error);
      addDebug(`💥 Fatal error: ${error.message}`);
      throw error;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <Loader className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
        <p className="text-lg text-gray-700 mb-2">{status}</p>
        <p className="text-sm text-gray-500">Please wait...</p>
        
        {/* Debug info for development */}
        {process.env.NODE_ENV === 'development' && debugInfo.length > 0 && (
          <div className="mt-6 p-4 bg-white rounded-lg shadow-sm text-left max-h-60 overflow-auto">
            <p className="text-xs font-bold text-gray-700 mb-2">Debug Log:</p>
            {debugInfo.map((info, idx) => (
              <p key={idx} className="text-xs text-gray-600 font-mono">{info}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
