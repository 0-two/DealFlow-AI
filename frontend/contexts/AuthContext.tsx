'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase, getUserProfile, signOut as supabaseSignOut, UserProfile } from '@/lib/supabase';
import type { Session } from '@supabase/supabase-js';

interface AuthContextType {
  session: Session | null;
  profile: UserProfile | null;
  loading: boolean;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  switchRole: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  session: null,
  profile: null,
  loading: true,
  signOut: async () => {},
  refreshProfile: async () => {},
  switchRole: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let isMounted = true;

    // Get initial session with timeout
    const initAuth = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (!isMounted) return;
        
        if (error) {
          console.error('Error getting session:', error);
          setLoading(false);
          return;
        }

        setSession(session);
        
        if (session?.user) {
          await loadUserProfile(session.user.id);
        } else {
          setLoading(false);
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Set a timeout to prevent infinite loading
    const timeoutId = setTimeout(() => {
      if (isMounted && loading) {
        console.warn('Auth initialization timed out');
        setLoading(false);
      }
    }, 5000);

    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (!isMounted) return;
        
        setSession(session);
        
        if (event === 'SIGNED_IN' && session?.user) {
          await loadUserProfile(session.user.id);
        } else if (event === 'SIGNED_OUT') {
          setProfile(null);
          localStorage.removeItem('userRole');
          localStorage.removeItem('userProfile');
          // Don't redirect here - let the calling function handle it
        }
        
        setLoading(false);
      }
    );

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
      subscription.unsubscribe();
    };
  }, [router]);

  const loadUserProfile = async (userId: string) => {
    try {
      const userProfile = await getUserProfile(userId);
      
      if (userProfile) {
        // Check if remember me is still valid
        if (userProfile.remember_me && userProfile.remember_me_expires) {
          const expiresAt = new Date(userProfile.remember_me_expires);
          if (expiresAt <= new Date()) {
            // Remember me expired, sign out
            await supabaseSignOut();
            setProfile(null);
            setLoading(false);
            return;
          }
        } else if (!userProfile.remember_me) {
          // No remember me, check if it's a new session
          const lastLogin = localStorage.getItem('lastLogin');
          const now = Date.now();
          
          if (lastLogin && now - parseInt(lastLogin) > 24 * 60 * 60 * 1000) {
            // More than 24 hours since last login without remember me
            await supabaseSignOut();
            setProfile(null);
            setLoading(false);
            return;
          }
        }

        setProfile(userProfile);
        localStorage.setItem('userRole', userProfile.role);
        localStorage.setItem('userProfile', JSON.stringify(userProfile));
        localStorage.setItem('lastLogin', Date.now().toString());
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
    }
    
    setLoading(false);
  };

  const refreshProfile = async () => {
    if (session?.user) {
      await loadUserProfile(session.user.id);
    }
  };

  const signOut = async () => {
    await supabaseSignOut();
    setSession(null);
    setProfile(null);
  };

  const switchRole = async () => {
    // Clear local storage and sign out completely
    localStorage.removeItem('userRole');
    localStorage.removeItem('userProfile');
    localStorage.removeItem('pendingRole');
    sessionStorage.removeItem('pendingRole');
    setProfile(null);
    setSession(null);
    // Sign out from Supabase
    await supabaseSignOut();
    // Redirect to role select (not login, so they can choose a new role)
    router.push('/role-select');
  };

  return (
    <AuthContext.Provider value={{ session, profile, loading, signOut, refreshProfile, switchRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
