const { createClient } = require('@supabase/supabase-js');
const url = 'https://ozeiymkbxtrqqdoxtmhm.supabase.co';
const key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96ZWl5bWtieHRycXFkb3h0bWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcyMjk1MzEsImV4cCI6MjEwMjgwNTUzMX0.6nQemY46XsG89kK5f_ONpAvrmI_buXX-VlpgLRY_sqs';
const client = createClient(url, key);

async function inspectDetailed() {
  const { data: complaints, error } = await client
    .from('complaints')
    .select('id, complaint_number, status, priority, category, photo_before_url, photo_after_url');

  if (error) {
    console.error('Error fetching complaints:', error);
    return;
  }

  console.log('Total complaints found in Supabase:', complaints.length);

  const statusCounts = {};
  const photos = new Set();

  complaints.forEach(c => {
    statusCounts[c.status] = (statusCounts[c.status] || 0) + 1;
    [c.photo_before_url, c.photo_after_url].forEach(p => {
      if (p) photos.add(p);
    });
  });

  console.log('Status breakdown:', statusCounts);
  console.log('Unique photo URLs count:', photos.size);
  console.log('Sample photo URLs:', Array.from(photos).slice(0, 15));

  // Check bucket 'issues' directly
  const { data: issuesFiles, error: issuesErr } = await client.storage.from('issues').list('', { limit: 100 });
  console.log('Direct list bucket "issues" root:', issuesFiles ? issuesFiles.length : 0, issuesErr ? issuesErr.message : '');
  if (issuesFiles && issuesFiles.length > 0) {
    console.log('Issues files:', issuesFiles.map(f => f.name));
  }

  const { data: issuesUploads, error: issuesUpErr } = await client.storage.from('issues').list('uploads', { limit: 100 });
  console.log('Direct list bucket "issues"/uploads:', issuesUploads ? issuesUploads.length : 0, issuesUpErr ? issuesUpErr.message : '');
  if (issuesUploads && issuesUploads.length > 0) {
    console.log('Issues uploads files:', issuesUploads.map(f => f.name));
  }

  // Also check complaint_status_history
  const { count: cshCount } = await client.from('complaint_status_history').select('*', { count: 'exact', head: true });
  console.log('complaint_status_history total count:', cshCount);
}

inspectDetailed().catch(console.error);
