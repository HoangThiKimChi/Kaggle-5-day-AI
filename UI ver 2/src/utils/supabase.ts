import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    "Supabase credentials (VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY) are missing in environment variables. " +
    "Authentication and saving progress will be disabled or fail until these keys are configured."
  );
}

export const supabase = createClient(
  supabaseUrl || 'https://placeholder-url.supabase.co', 
  supabaseAnonKey || 'placeholder-anon-key'
);
