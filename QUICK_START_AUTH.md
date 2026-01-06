# 🚀 Quick Start - Authentication Setup

## Prerequisites
- Supabase account
- Google Cloud account (for OAuth)
- Node.js installed

## 5-Minute Setup

### Step 1: Supabase Setup (2 min)
```bash
# 1. Create project at https://supabase.com
# 2. Copy Project URL and anon key from Settings → API
# 3. Run SQL in SQL Editor:
```
Copy contents from `supabase_schema.sql` and run it.

### Step 2: Google OAuth (2 min)
```bash
# 1. Go to https://console.cloud.google.com/
# 2. Create OAuth client ID
# 3. Add redirect URI: https://YOUR-PROJECT.supabase.co/auth/v1/callback
# 4. Copy Client ID and Secret
# 5. Paste in Supabase → Authentication → Providers → Google
```

### Step 3: Environment Variables (30 sec)
```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Supabase credentials
```

### Step 4: Install & Run (30 sec)
```bash
npm install
npm run dev
```

## Test It!
1. Visit http://localhost:3000/login
2. Choose Founder or Investor
3. Sign in with Google
4. ✅ You're in!

## What You Get
✅ Google OAuth authentication  
✅ Role-based access (Founder/Investor)  
✅ Remember me for 30 days  
✅ Auto-login on return  
✅ Secure logout  
✅ Protected routes  
✅ Role locked per account  

## Need Help?
See detailed instructions in `SUPABASE_SETUP.md` or `AUTHENTICATION_README.md`
