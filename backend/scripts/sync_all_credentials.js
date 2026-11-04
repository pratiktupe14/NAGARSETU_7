const { createClient } = require('@supabase/supabase-js');
const bcrypt = require('bcryptjs');
const { query } = require('../src/config/db');

const url = 'https://ozeiymkbxtrqqdoxtmhm.supabase.co';
const key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96ZWl5bWtieHRycXFkb3h0bWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcyMjk1MzEsImV4cCI6MjEwMjgwNTUzMX0.6nQemY46XsG89kK5f_ONpAvrmI_buXX-VlpgLRY_sqs';
const supabase = createClient(url, key);

async function syncAll() {
  const headHash = bcrypt.hashSync('head@123', 10);
  const staffHash = bcrypt.hashSync('staff@123', 10);
  const adminHash = bcrypt.hashSync('admin@123', 10);

  // 1. Supabase update department heads
  const { data: deptHeads, error: errH } = await supabase
    .from('users')
    .update({ password_hash: headHash })
    .eq('role', 'department_head')
    .select('id, email, name');
  console.log('Supabase updated dept heads:', deptHeads ? deptHeads.length : 0, errH);

  // 2. Supabase update field staff
  const { data: staff, error: errS } = await supabase
    .from('users')
    .update({ password_hash: staffHash })
    .eq('role', 'service_staff')
    .select('id, email, name');
  console.log('Supabase updated staff:', staff ? staff.length : 0, errS);

  // 3. Supabase update admin
  const { data: admins, error: errA } = await supabase
    .from('users')
    .update({ password_hash: adminHash })
    .eq('email', 'admin@nagarsetu.gov.in')
    .select('id, email, name');
  console.log('Supabase updated admin:', admins ? admins.length : 0, errA);

  // 4. Local SQLite update
  await query("UPDATE users SET password_hash = ? WHERE role = 'department_head'", [headHash]);
  await query("UPDATE users SET password_hash = ? WHERE role = 'service_staff'", [staffHash]);
  await query("UPDATE users SET password_hash = ? WHERE email = 'admin@nagarsetu.gov.in'", [adminHash]);
  console.log('Local SQLite updated for dept heads, staff, and admin');
}

syncAll()
  .then(() => {
    console.log('Credential synchronization complete.');
    process.exit(0);
  })
  .catch((e) => {
    console.error('Credential sync error:', e);
    process.exit(1);
  });

