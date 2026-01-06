# Supabase Authentication Setup Guide

## Prerequisites
- A Supabase account (https://supabase.com)
- Node.js installed

## Step 1: Create a Supabase Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Fill in:
   - Name: DealFlow-AI
   - Database Password: (choose a strong password)
   - Region: (choose closest to your users)
4. Wait for project to be created

## Step 2: Get Your Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy the following:
   - Project URL (under "Project URL")
   - anon/public key (under "Project API keys" → "anon public")

## Step 3: Configure Environment Variables

1. In the `frontend` directory, create a `.env.local` file:
   ```bash
   cp .env.local.example .env.local
   ```

2. Edit `.env.local` and add your Supabase credentials:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## Step 4: Run Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the contents of `supabase_schema.sql` from the project root
4. Paste into the SQL editor
5. Click "Run" to execute the schema

This will create:
- `user_profiles` table
- Row Level Security policies
- Indexes for performance

## Step 5: Enable Google OAuth

1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Find "Google" in the list and click on it
3. Enable the provider
4. You'll need to set up Google OAuth credentials:

### Setting up Google OAuth:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Configure consent screen if not done already
6. Choose **Web application**
7. Add authorized redirect URIs:
   ```
   https://your-project-ref.supabase.co/auth/v1/callback
   ```
8. Copy the **Client ID** and **Client Secret**

### Back in Supabase:

1. Paste Google **Client ID** in Supabase
2. Paste Google **Client Secret** in Supabase
3. Click "Save"

## Step 6: Install Dependencies

```bash
cd frontend
npm install
```

## Step 7: Run the Application

```bash
npm run dev
```

Visit `http://localhost:3000/login` to test the authentication.

## Testing the Flow

1. Go to `/login`
2. Select your role (Founder or Investor)
3. Click "Continue with Google"
4. Authorize with your Google account
5. You'll be redirected back and logged in
6. Your role is locked to your account
7. Check "Remember me for 30 days" to stay logged in

## Important Notes

### Role Locking
- Once a user selects a role (founder/investor) and signs in, that role is permanently assigned to their account
- Users cannot switch between roles without creating a new account
- This is enforced in the database and auth callback

### Remember Me Feature
- When enabled, users stay logged in for 30 days
- The expiry is stored in the `remember_me_expires` column
- On each app load, the system checks if remember me is still valid
- If expired or not set, users must log in again

### Security
- Row Level Security (RLS) is enabled on user_profiles table
- Users can only access their own profile data
- Auth tokens are stored securely in localStorage
- Sessions are validated on the server side

## Troubleshooting

### "Failed to create user profile"
- Check that the SQL schema was run successfully
- Verify RLS policies are enabled
- Check Supabase logs in dashboard

### Google OAuth not working
- Verify redirect URI matches exactly in Google Console
- Check that Google OAuth is enabled in Supabase
- Ensure client ID and secret are correct

### "Role mismatch" error
- This means the user already has an account with a different role
- They need to sign out and create a new account or use a different email

### Auto-login not working
- Check if remember me was enabled during login
- Verify `remember_me_expires` is set in database
- Check browser console for errors
