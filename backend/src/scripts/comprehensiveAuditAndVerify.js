const path = require('path');
const fs = require('fs');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });
require('dotenv').config({ path: path.join(__dirname, '../../../frontend/.env') });
const { createClient } = require('@supabase/supabase-js');
const sqlite3 = require('sqlite3').verbose();

async function runComprehensiveAudit() {
  console.log('========================================================================');
  console.log('  NAGARSETU 3.1 — COMPREHENSIVE COMPLAINT & PRODUCTION DATABASE AUDIT   ');
  console.log('========================================================================\n');

  const supabaseUrl = 'https://ozeiymkbxtrqqdoxtmhm.supabase.co';
  const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96ZWl5bWtieHRycXFkb3h0bWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcyMjk1MzEsImV4cCI6MjEwMjgwNTUzMX0.6nQemY46XsG89kK5f_ONpAvrmI_buXX-VlpgLRY_sqs';
  const supabase = createClient(supabaseUrl, supabaseKey);

  // 1. SUPABASE POSTGRESQL AUDIT
  console.log('--- 1. SUPABASE PRODUCTION AUDIT (https://ozeiymkbxtrqqdoxtmhm.supabase.co) ---');
  
  // Complaints counts
  const { data: complaints, error: cErr } = await supabase.from('complaints').select('id, complaint_number, status, priority, category');
  const complaintCount = complaints ? complaints.length : 0;
  console.log(`\n• Total Complaints in Supabase: ${complaintCount}`);

  const statusMap = {
    'Submitted': 0,
    'Pending': 0,
    'In Progress': 0,
    'Staff Assigned': 0,
    'Resolved': 0,
    'Resolution Submitted': 0,
    'Reopened': 0
  };

  if (complaints) {
    complaints.forEach(c => {
      const s = c.status || 'Unknown';
      statusMap[s] = (statusMap[s] || 0) + 1;
    });
  }

  console.log('  Breakdown by status:');
  for (const [st, count] of Object.entries(statusMap)) {
    console.log(`    - ${st}: ${count}`);
  }

  // Child tables
  const { count: cshCount } = await supabase.from('complaint_status_history').select('*', { count: 'exact', head: true });
  console.log(`• complaint_status_history rows: ${cshCount || 0}`);

  const { count: taskCount } = await supabase.from('task_assignments').select('*', { count: 'exact', head: true });
  console.log(`• task_assignments rows: ${taskCount || 0}`);

  const { count: feedbackCount } = await supabase.from('complaint_feedback').select('*', { count: 'exact', head: true });
  console.log(`• complaint_feedback rows: ${feedbackCount || 0}`);

  // Preserved Core Tables
  console.log('\n• Preserved System Entities:');
  const { count: usersCount } = await supabase.from('users').select('*', { count: 'exact', head: true });
  console.log(`    - users: ${usersCount || 0}`);

  const { count: profilesCount } = await supabase.from('profiles').select('*', { count: 'exact', head: true });
  console.log(`    - profiles: ${profilesCount || 0}`);

  const { count: deptsCount } = await supabase.from('departments').select('*', { count: 'exact', head: true });
  console.log(`    - departments: ${deptsCount || 0}`);

  const { count: headsCount } = await supabase.from('department_heads').select('*', { count: 'exact', head: true });
  console.log(`    - department_heads: ${headsCount || 0}`);

  const { count: rolesCount } = await supabase.from('user_roles').select('*', { count: 'exact', head: true });
  console.log(`    - user_roles: ${rolesCount || 0}`);

  // Storage audit
  console.log('\n--- 2. ATTACHMENT & STORAGE AUDIT ---');
  const { data: bucketFiles } = await supabase.storage.from('issues').list('');
  console.log(`• Supabase Storage bucket 'issues' (root): ${bucketFiles ? bucketFiles.length : 0} objects`);

  const { data: uploadBucketFiles } = await supabase.storage.from('issues').list('uploads');
  console.log(`• Supabase Storage bucket 'issues' (uploads/): ${uploadBucketFiles ? uploadBucketFiles.length : 0} objects`);

  const localUploadsDir = path.join(__dirname, '../../uploads');
  if (fs.existsSync(localUploadsDir)) {
    const localFiles = fs.readdirSync(localUploadsDir);
    console.log(`• Local backend/uploads/ directory: ${localFiles.length} files: ${JSON.stringify(localFiles)}`);
  }

  // 3. LOCAL SQLITE AUDIT
  console.log('\n--- 3. LOCAL SQLITE AUDIT (backend/nagarsetu.sqlite) ---');
  const sqliteDbPath = path.join(__dirname, '../../nagarsetu.sqlite');
  if (fs.existsSync(sqliteDbPath)) {
    const sdb = new sqlite3.Database(sqliteDbPath, sqlite3.OPEN_READONLY);
    await new Promise((res) => {
      sdb.get('SELECT COUNT(*) as count FROM complaints;', (err, row) => {
        console.log(`• SQLite complaints count: ${row ? row.count : 0}`);
        res();
      });
    });
    await new Promise((res) => {
      sdb.get('SELECT COUNT(*) as count FROM complaint_status_history;', (err, row) => {
        console.log(`• SQLite complaint_status_history count: ${row ? row.count : 0}`);
        res();
      });
    });
    sdb.close();
  }

  console.log('\n========================================================================');
  console.log(`VERIFICATION SUMMARY: ${complaintCount === 0 ? '✓ ALL ZERO (Clean)' : '⚠️ ATTENTION: ' + complaintCount + ' complaints exist in production Supabase'}`);
  console.log('========================================================================\n');
}

runComprehensiveAudit().catch(console.error);
