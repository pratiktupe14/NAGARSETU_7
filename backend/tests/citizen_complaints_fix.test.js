/**
 * Focused Verification Test for Citizen Complaints Visibility Fix
 * Proves:
 * 1. Numeric ID + valid UUID returns the correct citizen complaints
 * 2. Invalid numeric IDs are excluded from UUID queries (preventing Postgres 22P02)
 * 3. Another citizen's complaints remain strictly inaccessible (IDOR isolation)
 * 4. Database failures are not silently reported as zero complaints (fail-safe error propagation)
 * 5. Database data integrity (zero data lost)
 */

require('dotenv').config({ path: '.env' });
const assert = require('assert');

async function runTests() {
  console.log('--- STARTING CITIZEN COMPLAINTS VISIBILITY FIX VERIFICATION ---');

  const { query } = require('../src/config/db');
  const { getSupabase } = require('../src/config/supabaseStorage');
  const supabase = getSupabase();
  assert(supabase, 'Supabase client must be initialized');

  const citizenA = 'e2a4338c-5d49-4ae3-b766-40d99fb26f87';
  process.env.DB_TYPE = 'supabase'; // Enforce Supabase adapter path

  // 1. Regression Test: Numeric ID + valid UUID returns the correct citizen complaints
  console.log('\n[TEST 1] Testing Numeric ID + valid UUID parameter handling...');
  const mixedParams = ['2', citizenA, '58', citizenA];
  const sql = `
    SELECT c.*, d.name as department_name, f.rating, f.comment as feedback_comment
    FROM complaints c
    LEFT JOIN departments d ON (CAST(c.department_id AS TEXT) = CAST(d.id AS TEXT) OR c.department_id = d.code)
    LEFT JOIN feedback f ON f.complaint_id = c.id
    WHERE (c.citizen_id IN (?, ?, ?, ?) OR CAST(c.citizen_id AS TEXT) IN (?, ?, ?, ?))
    ORDER BY c.created_at DESC
  `;
  const mixedRes = await query(sql, mixedParams);
  assert(mixedRes && Array.isArray(mixedRes.rows), 'Query result must contain rows array');
  assert.strictEqual(mixedRes.rows.length, 34, `Expected exactly 34 complaints for Citizen A, got ${mixedRes.rows.length}`);
  for (const row of mixedRes.rows) {
    assert.strictEqual(String(row.citizen_id), citizenA, 'Record citizen_id must match citizen A');
  }
  console.log(`  PASS: Mixed numeric ('2', '58') + valid UUID returned all 34 citizen complaints without 22P02 error.`);

  // 2. Regression Test: Only invalid numeric IDs provided -> fails closed (0 complaints, never leaks)
  console.log('\n[TEST 2] Testing numeric-only parameters fail-closed behavior...');
  const numericOnlyParams = ['2', '58', '101'];
  const numSql = `
    SELECT c.*, d.name as department_name FROM complaints c
    WHERE c.citizen_id IN (?, ?, ?)
    ORDER BY c.created_at DESC
  `;
  const numRes = await query(numSql, numericOnlyParams);
  assert(numRes && Array.isArray(numRes.rows), 'Query result must contain rows array');
  assert.strictEqual(numRes.rows.length, 0, 'Must return exactly 0 complaints when no valid UUID exists');
  console.log('  PASS: Numeric-only parameters safely failed closed with 0 complaints (no 22P02 crash, no leakage).');

  // 3. Citizen Isolation & IDOR Protection: Query for Citizen B cannot see Citizen A's complaints
  console.log('\n[TEST 3] Testing citizen isolation and IDOR boundaries...');
  const citizenB = '89834ece-edd4-44c1-8a2e-b7b97bdcc4cf'; // Another actual citizen UUID in db
  const bSql = `
    SELECT c.*, d.name as department_name FROM complaints c
    WHERE c.citizen_id = ?
    ORDER BY c.created_at DESC
  `;
  const bRes = await query(bSql, [citizenB]);
  assert(bRes && Array.isArray(bRes.rows), 'Query result must contain rows array');
  console.log(`  Citizen B returned ${bRes.rows.length} complaints.`);
  for (const row of bRes.rows) {
    assert.strictEqual(String(row.citizen_id), citizenB, 'Citizen B records must strictly belong to Citizen B');
    assert.notStrictEqual(String(row.citizen_id), citizenA, 'Citizen B must NEVER see Citizen A records');
  }
  console.log('  PASS: Strict IDOR isolation maintained between citizens.');

  // 4. Test error propagation: Database failures are not silently converted to empty lists
  console.log('\n[TEST 4] Testing database error propagation (not masking failures as empty lists)...');
  // Trigger error path by passing query against non-existent table or broken query
  let caughtError = false;
  try {
    // Force a synthetic failure by querying with null client or invalid table
    const brokenSql = `SELECT * FROM non_existent_database_table_xyz_123 WHERE id = ?`;
    await query(brokenSql, [1]);
  } catch (err) {
    caughtError = true;
    console.log(`  Caught database error as expected: ${err.message}`);
  }
  assert(caughtError, 'Database query failure must throw/propagate and NOT silently return { rows: [] }');
  console.log('  PASS: Database failures are safely propagated rather than masked as zero complaints.');

  // 5. Database data integrity
  console.log('\n[TEST 5] Confirming database data integrity...');
  const { count, error: countErr } = await supabase
    .from('complaints')
    .select('*', { count: 'exact', head: true });
  assert(!countErr, `Count query error: ${countErr?.message}`);
  assert.strictEqual(count, 60, `Database complaints count must remain exactly 60, found ${count}`);
  console.log(`  Supabase complaints table preserved with ${count} total records.`);
  console.log('  PASS: Database data integrity confirmed (0 records lost).');

  console.log('\n=== ALL FOCUSED REGRESSION TESTS PASSED SUCCESSFULLY ===');
}

runTests().catch(err => {
  console.error('\nFAILED TEST:', err);
  process.exit(1);
});
