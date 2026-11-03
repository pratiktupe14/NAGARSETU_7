const { createClient } = require('@supabase/supabase-js');

function getValidSupabaseConfig() {
  const urlCandidates = [
    process.env.SUPABASE_URL,
    process.env.VITE_SUPABASE_URL,
    process.env.PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_URL
  ];

  const keyCandidates = [
    process.env.SUPABASE_SERVICE_ROLE_KEY,
    process.env.SUPABASE_ANON_KEY,
    process.env.VITE_SUPABASE_ANON_KEY,
    process.env.PUBLIC_SUPABASE_ANON_KEY,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  ];

  const isValidUrl = (u) => {
    if (!u || typeof u !== 'string') return false;
    const s = u.trim();
    return (s.startsWith('http://') || s.startsWith('https://')) &&
      !s.includes('[Sensitive]') &&
      !s.includes('your-supabase') &&
      !s.includes('your-project') &&
      !s.includes('placeholder') &&
      !s.includes('example');
  };

  const isValidKey = (k) => {
    if (!k || typeof k !== 'string') return false;
    const s = k.trim();
    return s.length > 20 &&
      !s.includes('[Sensitive]') &&
      !s.includes('your_supabase') &&
      !s.includes('your-supabase') &&
      !s.includes('your_service_role') &&
      !s.includes('placeholder') &&
      !s.includes('here');
  };

  const validUrlMatch = urlCandidates.find(isValidUrl);
  const validKeyMatch = keyCandidates.find(isValidKey);

  const validUrl = validUrlMatch ? validUrlMatch.trim() : '';
  const validKey = validKeyMatch ? validKeyMatch.trim() : '';

  return { url: validUrl, key: validKey };
}

let supabaseInstance = null;

function getSupabase() {
  if (supabaseInstance) return supabaseInstance;

  const { url, key } = getValidSupabaseConfig();
  if (url && key) {
    try {
      supabaseInstance = createClient(url, key, {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false
        }
      });
      return supabaseInstance;
    } catch (e) {
      console.warn('[SUPABASE STORAGE] Initialization note:', e.message);
    }
  }
  return null;
}

// Initial bootstrap attempt
getSupabase();

/**
 * Uploads a file buffer to Supabase Storage bucket (default 'issues')
 * and returns the full public HTTPS URL.
 * 
 * @param {Buffer} buffer 
 * @param {string} filename 
 * @param {string} mimetype 
 * @param {string} bucketName 
 * @returns {Promise<{ publicUrl: string, filePath: string }>}
 */
async function uploadBufferToSupabase(buffer, filename, mimetype = 'image/jpeg', bucketName = 'issues') {
  const client = getSupabase();
  if (!client) {
    throw new Error('Supabase client is not configured on the backend. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.');
  }

  const cleanFilename = `${Date.now()}_${filename.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
  const filePath = `uploads/${cleanFilename}`;

  const { data, error } = await client.storage
    .from(bucketName)
    .upload(filePath, buffer, {
      contentType: mimetype,
      cacheControl: '3600',
      upsert: true
    });

  if (error) {
    console.error('[SUPABASE STORAGE ERROR]', error.message);
    throw new Error(`Supabase Storage upload failed: ${error.message}`);
  }

  const { data: publicUrlData } = client.storage
    .from(bucketName)
    .getPublicUrl(filePath);

  if (!publicUrlData || !publicUrlData.publicUrl) {
    throw new Error('Failed to retrieve public URL from Supabase Storage.');
  }

  return {
    publicUrl: publicUrlData.publicUrl,
    filePath: data.path || filePath
  };
}

module.exports = {
  get supabase() {
    return getSupabase();
  },
  getSupabase,
  uploadBufferToSupabase
};
