# 🔐 Authentication System Implementation

## Overview

Complete Google OAuth authentication system with Supabase, featuring role-based access control, remember me functionality, and secure session management.

## ✨ Features Implemented

### 1. **Google OAuth Authentication**
- Single Sign-On with Google accounts
- Secure token management
- Automatic session refresh

### 2. **Role Selection & Locking**
- Users choose role (Founder/Investor) before first login
- Role is **permanently locked** to account
- Cannot switch roles without new account
- Role mismatch detection prevents unauthorized access

### 3. **Remember Me (30 Days)**
- Optional "Remember me for 30 days" checkbox
- Auto-login on return visits if enabled
- Expiry tracked in database
- Automatic logout when expired

### 4. **Secure Session Management**
- Row Level Security (RLS) on user data
- JWT token validation
- Automatic session refresh
- Secure logout functionality

### 5. **Protected Routes**
- All main pages require authentication
- Role-based route protection
- Automatic redirect to login if unauthorized
- Loading states during auth checks

## 📁 Files Created/Modified

### **New Files:**
1. `frontend/lib/supabase.ts` - Supabase client & auth functions
2. `frontend/app/login/page.tsx` - Login page with role selection
3. `frontend/app/auth/callback/page.tsx` - OAuth callback handler
4. `frontend/contexts/AuthContext.tsx` - Global auth state management
5. `frontend/components/Auth/ProtectedRoute.tsx` - Route protection wrapper
6. `supabase_schema.sql` - Database schema
7. `SUPABASE_SETUP.md` - Setup instructions
8. `frontend/.env.local.example` - Environment variables template

### **Modified Files:**
1. `frontend/app/providers.tsx` - Added AuthProvider
2. `frontend/app/page.tsx` - Redirect logic based on auth
3. `frontend/app/chat/page.tsx` - Protected route implementation
4. `frontend/components/Layout/Header.tsx` - Logout functionality
5. `frontend/package.json` - Added @supabase/supabase-js dependency

## 🗄️ Database Schema

```sql
user_profiles table:
- id (UUID, primary key, references auth.users)
- email (TEXT, not null)
- role (TEXT, 'founder' or 'investor')
- full_name (TEXT, optional)
- remember_me (BOOLEAN, default false)
- remember_me_expires (TIMESTAMPTZ, nullable)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

## 🔄 Authentication Flow

### **First Time Login:**
```
1. User visits /login
2. Selects role (Founder/Investor)
3. Clicks "Continue with Google"
4. Optionally checks "Remember me for 30 days"
5. Redirected to Google OAuth
6. Returns to /auth/callback
7. Profile created with selected role
8. Redirected to /chat
```

### **Returning User (Remember Me Enabled):**
```
1. User visits site
2. AuthContext checks session
3. Validates remember_me_expires
4. If valid → Auto-login → /chat
5. If expired → Clear session → /login
```

### **Returning User (Remember Me Disabled):**
```
1. User visits site
2. No valid session found
3. Redirected to /login
```

### **Role Mismatch Protection:**
```
1. User logs in with existing account
2. System checks stored role vs. selected role
3. If mismatch → Logout → Error message
4. User must use correct role or different email
```

## 🔒 Security Features

### **Row Level Security (RLS)**
```sql
- Users can only view their own profile
- Users can only update their own profile
- Enforced at database level
```

### **Session Validation**
- Tokens validated on every request
- Automatic refresh before expiry
- Secure storage in localStorage
- HttpOnly cookies for sensitive data

### **Role Enforcement**
- Role checked on route access
- Protected API endpoints (backend)
- Cannot switch roles without new account
- Database constraint prevents invalid roles

## 🚀 Setup Instructions

### **1. Install Dependencies**
```bash
cd frontend
npm install
```

### **2. Configure Supabase**
Follow detailed instructions in `SUPABASE_SETUP.md`

### **3. Environment Variables**
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **4. Run Database Schema**
Execute `supabase_schema.sql` in Supabase SQL Editor

### **5. Enable Google OAuth**
Configure in Supabase Authentication settings

### **6. Start Application**
```bash
npm run dev
```

## 📱 Usage

### **For Users:**

1. **First Login:**
   - Go to `/login`
   - Choose Founder or Investor
   - Sign in with Google
   - Check "Remember me" to stay logged in for 30 days

2. **Using the App:**
   - All main pages are protected
   - Role-specific navigation and features
   - Logout button in header

3. **Logging Out:**
   - Click logout icon in header
   - Session cleared
   - Redirected to login

### **For Developers:**

1. **Protecting Routes:**
```tsx
import ProtectedRoute from '@/components/Auth/ProtectedRoute';

export default function MyPage() {
  return (
    <ProtectedRoute allowedRoles={['founder']}>
      <YourContent />
    </ProtectedRoute>
  );
}
```

2. **Accessing User Info:**
```tsx
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { session, profile, signOut } = useAuth();
  
  return (
    <div>
      <p>Role: {profile?.role}</p>
      <p>Email: {profile?.email}</p>
      <button onClick={signOut}>Logout</button>
    </div>
  );
}
```

3. **Checking Auth State:**
```tsx
const { session, profile, loading } = useAuth();

if (loading) return <Loader />;
if (!session) return <LoginPrompt />;
if (profile.role !== 'founder') return <Unauthorized />;
```

## 🧪 Testing Checklist

- [ ] Can select founder role and login
- [ ] Can select investor role and login
- [ ] Remember me enables auto-login
- [ ] Remember me expires after 30 days
- [ ] Cannot access app without login
- [ ] Cannot switch roles with same account
- [ ] Role mismatch shows error
- [ ] Logout works correctly
- [ ] Session persists on page refresh
- [ ] Protected routes redirect to login
- [ ] Role-based navigation works

## 🐛 Common Issues

### "Module not found: @supabase/supabase-js"
**Solution:** Run `npm install` in frontend directory

### "Invalid project URL"
**Solution:** Check `.env.local` has correct Supabase URL

### Google OAuth not working
**Solution:** Verify redirect URI in Google Cloud Console

### Auto-login not working
**Solution:** Check remember_me is enabled and not expired

### Role mismatch error
**Solution:** User trying to login with different role - must use correct role or new email

## 📚 Additional Resources

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Next.js Authentication](https://nextjs.org/docs/authentication)
- [Google OAuth Setup](https://developers.google.com/identity/protocols/oauth2)

## 🎯 Next Steps

Consider implementing:
- [ ] Email/password authentication option
- [ ] Password reset flow
- [ ] Email verification
- [ ] Two-factor authentication
- [ ] Social login with other providers
- [ ] Admin panel for user management
- [ ] Activity logging
