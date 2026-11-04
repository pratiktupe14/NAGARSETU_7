/**
 * Verification Test: NAGARSETU 3.1 Department Assignment & Portal Routing
 * 
 * Verifies:
 * 1. Unit tests for WTR, PWD, SAN, DRN resolution
 * 2. 8 mandatory test cases required by user:
 *    - Water Leakage → WTR
 *    - Water Pipeline Burst → WTR
 *    - Water Supply Interruption → WTR
 *    - Contaminated Water → WTR
 *    - Road Pothole → PWD
 *    - Garbage Accumulation → SAN
 *    - Blocked Drainage → DRN
 *    - Sewer Overflow → DRN
 * 3. AI prediction and frontend default override prevention
 * 4. Real DB persistence with correct canonical UUIDs
 * 5. Water Supply Department Head Portal retrieval isolation
 */

const assert = require('assert');
const { query } = require('../src/config/db');
const {
  resolveDepartmentByCode,
  resolveDepartmentByCodeSync,
  resolveDepartmentForComplaint
} = require('../src/services/departmentService');

async function runTests() {
  console.log('\n===============================================================');
  console.log('   NAGARSETU 3.1 - DEPARTMENT ROUTING VERIFICATION SUITE');
  console.log('===============================================================\n');

  let passed = 0;
  let total = 0;

  function expect(condition, message) {
    total++;
    if (condition) {
      console.log(`  [PASS] ${message}`);
      passed++;
    } else {
      console.error(`  [FAIL] ${message}`);
      throw new Error(`Assertion failed: ${message}`);
    }
  }

  // -------------------------------------------------------------
  // TEST SUITE 1: CANONICAL RESOLVER TESTS
  // -------------------------------------------------------------
  console.log('--- Test Suite 1: Canonical Department Resolution ---');

  // WTR Tests
  const wtrByCode = await resolveDepartmentByCode('WTR');
  expect(wtrByCode.code === 'WTR' && wtrByCode.id === 'ead370cc-459c-44f0-899f-8a97f0928beb', 'Resolves "WTR" to Water Supply & Sewerage Board');

  const wtrByName = await resolveDepartmentByCode('Water Supply & Sewerage Board');
  expect(wtrByName.code === 'WTR' && wtrByName.id === 'ead370cc-459c-44f0-899f-8a97f0928beb', 'Resolves "Water Supply & Sewerage Board" to WTR');

  const wtrByAlias = await resolveDepartmentByCode('Water Pipe Leakage');
  expect(wtrByAlias.code === 'WTR', 'Resolves alias "Water Pipe Leakage" to WTR');

  const wtrById = await resolveDepartmentByCode('3');
  expect(wtrById.code === 'WTR', 'Resolves registry_id "3" to WTR');

  // PWD Tests
  const pwdByCode = await resolveDepartmentByCode('PWD');
  expect(pwdByCode.code === 'PWD' && pwdByCode.id === '8ed9f760-1314-427c-a515-c2a54d6df6d8', 'Resolves "PWD" to Public Works Department');

  const pwdByName = await resolveDepartmentByCode('Public Works Department');
  expect(pwdByName.code === 'PWD', 'Resolves "Public Works Department" to PWD');

  const pwdByAlias = await resolveDepartmentByCode('Road Pothole');
  expect(pwdByAlias.code === 'PWD', 'Resolves alias "Road Pothole" to PWD');

  // SAN Tests
  const sanByCode = await resolveDepartmentByCode('SAN');
  expect(sanByCode.code === 'SAN' && sanByCode.id === '9cabc1f2-fd10-48dd-a5cb-01d05197de22', 'Resolves "SAN" to Sanitation & Waste Management');

  const sanByName = await resolveDepartmentByCode('Sanitation & Waste Management');
  expect(sanByName.code === 'SAN', 'Resolves "Sanitation & Waste Management" to SAN');

  const sanByAlias = await resolveDepartmentByCode('Garbage accumulation');
  expect(sanByAlias.code === 'SAN', 'Resolves alias "Garbage accumulation" to SAN');

  // DRN Tests
  const drnByCode = await resolveDepartmentByCode('DRN');
  expect(drnByCode.code === 'DRN' && drnByCode.id === 'ee73cb82-cc47-4333-b7d6-4491353c1354', 'Resolves "DRN" to Drainage & Sewage Department');

  const drnByName = await resolveDepartmentByCode('Drainage & Sewage Department');
  expect(drnByName.code === 'DRN', 'Resolves "Drainage & Sewage Department" to DRN');

  const drnByAlias = await resolveDepartmentByCode('Blocked sewer overflow');
  expect(drnByAlias.code === 'DRN', 'Resolves alias "Blocked sewer overflow" to DRN');

  // -------------------------------------------------------------
  // TEST SUITE 2: MANDATORY 8 CIVIC CASES (Section 7)
  // -------------------------------------------------------------
  console.log('\n--- Test Suite 2: Mandatory 8 Civic Routing Cases ---');

  // Case 1: Submit Water Leakage → WTR
  const c1 = resolveDepartmentForComplaint({ title: 'Water Leakage', category: 'Water', description: 'Water leaking from municipal pipe' });
  expect(c1.code === 'WTR' && c1.id === 'ead370cc-459c-44f0-899f-8a97f0928beb', 'Case 1: Water Leakage routes to WTR (ead370cc-459c-44f0-899f-8a97f0928beb)');

  // Case 2: Submit Water Pipeline Burst → WTR
  const c2 = resolveDepartmentForComplaint({ title: 'Water Pipeline Burst', category: 'Water', description: 'Major burst on main line' });
  expect(c2.code === 'WTR' && c2.id === 'ead370cc-459c-44f0-899f-8a97f0928beb', 'Case 2: Water Pipeline Burst routes to WTR');

  // Case 3: Submit Water Supply Interruption → WTR
  const c3 = resolveDepartmentForComplaint({ title: 'Water Supply Interruption', category: 'Water', description: 'No potable water supply for 3 days' });
  expect(c3.code === 'WTR' && c3.id === 'ead370cc-459c-44f0-899f-8a97f0928beb', 'Case 3: Water Supply Interruption routes to WTR');

  // Case 4: Submit Contaminated Water → WTR
  const c4 = resolveDepartmentForComplaint({ title: 'Contaminated Water', category: 'Water', description: 'Drinking water is discolored and murky' });
  expect(c4.code === 'WTR' && c4.id === 'ead370cc-459c-44f0-899f-8a97f0928beb', 'Case 4: Contaminated Water routes to WTR');

  // Case 5: Submit Road Pothole → PWD
  const c5 = resolveDepartmentForComplaint({ title: 'Road Pothole', category: 'Roads', description: 'Deep cavity in asphalt carriageway' });
  expect(c5.code === 'PWD' && c5.id === '8ed9f760-1314-427c-a515-c2a54d6df6d8', 'Case 5: Road Pothole routes to PWD (8ed9f760-1314-427c-a515-c2a54d6df6d8)');

  // Case 6: Submit Garbage Accumulation → SAN
  const c6 = resolveDepartmentForComplaint({ title: 'Garbage Accumulation', category: 'Sanitation', description: 'Rotting solid waste piled on corner' });
  expect(c6.code === 'SAN' && c6.id === '9cabc1f2-fd10-48dd-a5cb-01d05197de22', 'Case 6: Garbage Accumulation routes to SAN (9cabc1f2-fd10-48dd-a5cb-01d05197de22)');

  // Case 7: Submit Blocked Drainage → DRN
  const c7 = resolveDepartmentForComplaint({ title: 'Blocked Drainage', category: 'Drainage', description: 'Storm gutter clogged with silt and refuse' });
  expect(c7.code === 'DRN' && c7.id === 'ee73cb82-cc47-4333-b7d6-4491353c1354', 'Case 7: Blocked Drainage routes to DRN (ee73cb82-cc47-4333-b7d6-4491353c1354)');

  // Case 8: Submit Sewer Overflow → DRN
  const c8 = resolveDepartmentForComplaint({ title: 'Sewer Overflow', category: 'Drainage', description: 'Underground sewer manhole spilling onto roadway' });
  expect(c8.code === 'DRN' && c8.id === 'ee73cb82-cc47-4333-b7d6-4491353c1354', 'Case 8: Sewer Overflow routes to DRN');

  // -------------------------------------------------------------
  // TEST SUITE 3: AI & FRONTEND OVERRIDE GUARDS
  // -------------------------------------------------------------
  console.log('\n--- Test Suite 3: Anti-Override Guards ---');

  // Test that AI predictions cannot override water category with PWD
  const aiOverrideAttempt = resolveDepartmentForComplaint({
    category: 'Water',
    title: 'Water Leakage',
    description: 'Drinking water leaking from main line',
    ai_category: 'Roads',
    ai_specific_issue: 'Surface Defect',
    department: 'Public Works Department',
    department_id: '8ed9f760-1314-427c-a515-c2a54d6df6d8'
  });
  expect(aiOverrideAttempt.code === 'WTR', 'AI prediction of Roads cannot override explicit Water complaint into PWD');

  // Test that frontend default id: '1' cannot override water category
  const frontendDefaultAttempt = resolveDepartmentForComplaint({
    category: 'Water',
    title: 'Pipeline Leak',
    department_id: '1',
    department: 'Public Works Department'
  });
  expect(frontendDefaultAttempt.code === 'WTR', 'Frontend default department ID "1" cannot override Water category');

  // -------------------------------------------------------------
  // TEST SUITE 4: DATABASE PERSISTENCE & PORTAL RETRIEVAL
  // -------------------------------------------------------------
  console.log('\n--- Test Suite 4: Database Persistence & Department Head Portal Verification ---');

  const testComplaintNumber = `NS-${new Date().getFullYear()}-${Math.floor(100000 + Math.random() * 900000)}`;
  const waterDeptId = 'ead370cc-459c-44f0-899f-8a97f0928beb'; // WTR

  // Insert real test water complaint
  await query(
    `INSERT INTO complaints (
      complaint_number, citizen_id, title, description, category,
      department_id, priority, status, latitude, longitude,
      location_source, location_address,
      photo_before_url, photo_front_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      testComplaintNumber,
      '1',
      'Water pipeline leakage at Market Circle',
      'Continuous drinking water pipe burst flooding road near Market Circle',
      'Water',
      waterDeptId,
      'High',
      'Submitted',
      18.5204,
      73.8567,
      'manual_pin',
      'Market Circle, Ward 4',
      '/uploads/civic-test-water.jpg',
      '/uploads/civic-test-water.jpg'
    ]
  );

  console.log(`  [INFO] Inserted test water complaint: ${testComplaintNumber} with department_id: ${waterDeptId}`);

  // Query as Water Supply Department Head (Vikram Patil, department WTR)
  // Uses exact SQL from GET /api/department/complaints
  const wtrPortalQuery = await query(
    `SELECT c.id, c.complaint_number, c.title, c.category, c.department_id, d.code as dept_code, d.name as dept_name
     FROM complaints c
     LEFT JOIN departments d ON c.department_id = d.id
     WHERE c.complaint_number = ? AND (c.department_id = ? OR d.code = 'WTR')`,
    [testComplaintNumber, waterDeptId]
  );

  expect(wtrPortalQuery.rows.length === 1, 'Complaint appears in Water Supply Department Head Portal');
  const record = wtrPortalQuery.rows[0];
  expect(record.dept_code === 'WTR', `Complaint dept_code is WTR (actual: ${record.dept_code})`);
  expect(record.department_id === waterDeptId, `Complaint department_id matches WTR UUID (${waterDeptId})`);

  // Query as PWD Department Head (Rahul Kumar, department PWD: 8ed9f760-1314-427c-a515-c2a54d6df6d8)
  const pwdPortalQuery = await query(
    `SELECT c.id, c.complaint_number, c.title, c.category, c.department_id, d.code as dept_code
     FROM complaints c
     LEFT JOIN departments d ON c.department_id = d.id
     WHERE c.complaint_number = ? AND (c.department_id = '8ed9f760-1314-427c-a515-c2a54d6df6d8' OR d.code = 'PWD')`,
    [testComplaintNumber]
  );

  expect(pwdPortalQuery.rows.length === 0, 'Complaint is strictly ISOLATED and does NOT leak into PWD Portal');

  console.log('\n===============================================================');
  console.log(`   ALL TESTS PASSED: ${passed}/${total} assertions succeeded!`);
  console.log('===============================================================\n');
}

runTests().catch(err => {
  console.error('\nTest failed with error:', err);
  process.exit(1);
});
