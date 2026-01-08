'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase, getUserProfile, signOut as supabaseSignOut, UserProfile, isSupabaseConfigured } from '@/lib/supabase';
import type { Session } from '@supabase/supabase-js';

interface AuthContextType {
  session: Session | null;
  profile: UserProfile | null;
  loading: boolean;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  switchRole: () => Promise<void>;
  isConfigured: boolean;
}

const AuthContext = createContext<AuthContextType>({
  session: null,
  profile: null,
  loading: true,
  signOut: async () => {},
  refreshProfile: async () => {},
  switchRole: async () => {},
  isConfigured: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let isMounted = true;

    // If Supabase is not configured, stop loading immediately
    if (!isSupabaseConfigured) {
      console.warn('Supabase not configured, skipping auth initialization');
      setLoading(false);
      return;
    }

    // Hydrate from localStorage early to reduce redirect flicker on refresh
    try {
      const cached = typeof window !== 'undefined' ? localStorage.getItem('userProfile') : null;
      if (cached) {
        const parsed = JSON.parse(cached) as UserProfile;
        setProfile(parsed);
      }
    } catch {}

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
        // If we have a cached profile, keep a softer loading state to avoid redirect flicker
        const cached = typeof window !== 'undefined' ? localStorage.getItem('userProfile') : null;
        if (!cached) setLoading(false);
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
        setProfile(userProfile);
        localStorage.setItem('userRole', userProfile.role);
        localStorage.setItem('userProfile', JSON.stringify(userProfile));
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
    localStorage.removeItem('pendingRememberMe');
    sessionStorage.removeItem('pendingRole');
    sessionStorage.removeItem('pendingRememberMe');
    setProfile(null);
    setSession(null);
    // Sign out from Supabase
    await supabaseSignOut();
    // Redirect to login where they can choose a new role
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ session, profile, loading, signOut, refreshProfile, switchRole, isConfigured: isSupabaseConfigured }}>
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
