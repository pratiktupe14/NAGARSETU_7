/**
 * End-to-End Test for NAGARSETU 3.1 Complaint Submission & Department Portal Isolation
 */

const http = require('http');
const app = require('../src/app');
const { query } = require('../src/config/db');

async function runE2ETest() {
  console.log('\n===============================================================');
  console.log('   NAGARSETU 3.1 - E2E COMPLAINT SUBMISSION & PORTAL TEST');
  console.log('===============================================================\n');

  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, resolve));
  const port = server.address().port;
  const baseUrl = `http://127.0.0.1:${port}`;
  console.log(`Test server running on ${baseUrl}`);

  try {
    // 1. Login as citizen Rahul Sharma
    const citizenLoginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul@citizen.nagarsetu.gov.in',
        password: 'password123'
      })
    });
    const citizenLoginData = await citizenLoginRes.json();
    if (!citizenLoginRes.ok || !citizenLoginData.token) {
      throw new Error(`Citizen login failed: ${JSON.stringify(citizenLoginData)}`);
    }
    const citizenToken = citizenLoginData.token;
    console.log('1. Obtained citizen auth token successfully.');

    // 2. Submit Water Complaint via POST /api/complaints/submit
    const randomOffset = Math.random() * 0.05 + 0.01;
    const waterComplaintPayload = {
      category: 'Water',
      title: 'Major main line pipe leakage near Deccan Gymkhana',
      description: 'Underground potable water supply line burst causing continuous high volume water loss',
      priority: 'High',
      department: 'Water Supply & Sewerage Board',
      latitude: 18.51 + randomOffset,
      longitude: 73.84 + randomOffset,
      location_source: 'live_gps',
      location_address: 'Deccan Gymkhana, Pune',
      photo_url: '/uploads/pipe_leak_front.jpg',
      photo_before_url: '/uploads/pipe_leak_front.jpg',
      photo_front_url: '/uploads/pipe_leak_front.jpg',
      photo_left_url: '/uploads/pipe_leak_left.jpg',
      angle_photos: [
        { slot: 1, angle: 'front', url: '/uploads/pipe_leak_front.jpg' },
        { slot: 2, angle: 'left', url: '/uploads/pipe_leak_left.jpg' }
      ]
    };

    const submitRes = await fetch(`${baseUrl}/api/complaints/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${citizenToken}`
      },
      body: JSON.stringify(waterComplaintPayload)
    });

    const submitData = await submitRes.json();
    console.log('2. Submission HTTP Status:', submitRes.status);
    console.log('   Submission response:', JSON.stringify(submitData, null, 2));

    if (!submitRes.ok) {
      throw new Error(`Submission failed with status ${submitRes.status}: ${JSON.stringify(submitData)}`);
    }

    const complaint = submitData.complaint || submitData.data || submitData;
    const complaintNumber = complaint.complaint_number;
    const assignedDeptId = complaint.department_id;
    const assignedDeptCode = complaint.department_code;

    console.log(`   Complaint Number: ${complaintNumber}`);
    console.log(`   Assigned Department ID: ${assignedDeptId}`);
    console.log(`   Assigned Department Code: ${assignedDeptCode}`);

    if (assignedDeptCode !== 'WTR' || assignedDeptId !== 'ead370cc-459c-44f0-899f-8a97f0928beb') {
      throw new Error(`FAIL: Water complaint assigned to wrong department: code=${assignedDeptCode}, id=${assignedDeptId}`);
    }
    console.log('   [SUCCESS] Water complaint assigned strictly to WTR!');

    // 3. Login as Water Supply Department Head (Vikram Patil)
    const wtrLoginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'vikram.patil@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    const wtrLoginData = await wtrLoginRes.json();
    if (!wtrLoginRes.ok) {
      throw new Error(`Water Dept Head login failed: ${JSON.stringify(wtrLoginData)}`);
    }
    const wtrToken = wtrLoginData.token;
    console.log('3. Water Supply Dept Head (Vikram Patil) logged in successfully.');

    // 4. Fetch complaints as Water Supply Dept Head
    const wtrComplaintsRes = await fetch(`${baseUrl}/api/department/complaints`, {
      headers: { 'Authorization': `Bearer ${wtrToken}` }
    });
    const wtrComplaintsData = await wtrComplaintsRes.json();
    const wtrComplaintsList = wtrComplaintsData.complaints || wtrComplaintsData.data || (Array.isArray(wtrComplaintsData) ? wtrComplaintsData : []);
    
    const foundInWtr = wtrComplaintsList.some(c => c.complaint_number === complaintNumber);
    console.log(`4. Complaint ${complaintNumber} found in Water Dept Head Portal: ${foundInWtr}`);
    if (!foundInWtr) {
      throw new Error('FAIL: Complaint was NOT visible in Water Supply Department Head Portal!');
    }
    console.log('   [SUCCESS] Verified complaint appears in Water Supply Department Head Portal!');

    // 5. Login as PWD Department Head (Rahul Kumar)
    const pwdLoginRes = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mobileOrEmail: 'rahul.kumar@nagarsetu.gov.in',
        password: 'head@123'
      })
    });
    const pwdLoginData = await pwdLoginRes.json();
    if (!pwdLoginRes.ok) {
      throw new Error(`PWD Dept Head login failed: ${JSON.stringify(pwdLoginData)}`);
    }
    const pwdToken = pwdLoginData.token;
    console.log('5. PWD Dept Head (Rahul Kumar) logged in successfully.');

    // 6. Fetch complaints as PWD Dept Head
    const pwdComplaintsRes = await fetch(`${baseUrl}/api/department/complaints`, {
      headers: { 'Authorization': `Bearer ${pwdToken}` }
    });
    const pwdComplaintsData = await pwdComplaintsRes.json();
    const pwdComplaintsList = pwdComplaintsData.complaints || pwdComplaintsData.data || (Array.isArray(pwdComplaintsData) ? pwdComplaintsData : []);
    
    const foundInPwd = pwdComplaintsList.some(c => c.complaint_number === complaintNumber);
    console.log(`6. Complaint ${complaintNumber} found in PWD Portal: ${foundInPwd}`);
    if (foundInPwd) {
      throw new Error('FAIL: Water complaint incorrectly leaked into PWD Department Head Portal!');
    }
    console.log('   [SUCCESS] Verified water complaint is strictly ISOLATED from PWD Portal!');

    console.log('\n===============================================================');
    console.log('   ALL E2E CHECKS PASSED: 100% SUCCESSFUL DEPARTMENT ROUTING!');
    console.log('===============================================================\n');
  } finally {
    server.close();
  }
}

runE2ETest().catch(err => {
  console.error('\nE2E Test failed:', err);
  process.exit(1);
});
