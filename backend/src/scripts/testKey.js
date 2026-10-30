const fs = require('fs');
const path = require('path');

const envPath = path.resolve(__dirname, '../../../.vercel/.env.production.local');
if (fs.existsSync(envPath)) {
  const content = fs.readFileSync(envPath, 'utf8');
  for (const line of content.split('\n')) {
    if (line.startsWith('SUPABASE_SERVICE_ROLE_KEY=')) {
      const val = line.substring('SUPABASE_SERVICE_ROLE_KEY='.length).trim().replace(/^['"]|['"]$/g, '');
      console.log('Key length:', val.length);
      console.log('Starts with eyJ?:', val.startsWith('eyJ'));
      console.log('Is placeholder?:', val.includes('placeholder') || val.includes('your_'));
    }
  }
}
