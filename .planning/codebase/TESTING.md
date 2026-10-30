# Testing Patterns

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1

## Test Infrastructure & Runners

**Backend Test Harness:**
- **Runner**: Custom lightweight Node.js test runner in [`backend/tests/run_tests.js`](file:///d:/NAGARSETU/NAGARSETU%203.1/backend/tests/run_tests.js).
- **Execution Mode**: Executes suites sequentially with timing, test pass/fail tallies, colorized terminal reporting, and automated error dumps.
- **Assertion Engine**: Native Node.js `assert` module (`assert.strictEqual`, `assert.ok`, `assert.deepStrictEqual`).
- **Command**:
  ```bash
  # Run all 32 backend test suites
  npm test --workspace=backend
  # Or run directly from backend directory:
  node tests/run_tests.js
  ```

**Frontend Build & Static Type Verification:**
- **Engine**: TypeScript Compiler (`tsc`) & Vite build bundler.
- **Verification Rule**: Zero TypeScript errors (`0 TS errors`) and zero unresolved module imports.
- **Command**:
  ```bash
  npm run build --workspace=frontend
  ```

**Python AI Service Tests:**
- **Runner**: `pytest` running inside the Python virtual environment.
- **Command**:
  ```bash
  cd ai_service && pytest tests/
  ```

## Test Suite Inventory (`backend/tests/`)

The backend maintains 32 automated test suites covering all critical civic operations:

| Category | Key Test Suites | Focus & Verification |
| :--- | :--- | :--- |
| **Authentication & RBAC** | `auth_security.test.js`<br>`role_routing_and_auth.test.js`<br>`hod_assignment_rbac.test.js` | JWT issuance, password hashing, role gating, unauthorized access rejection. |
| **Complaint Lifecycle** | `complaint_submission.test.js`<br>`complaint_persistence_regression.test.js`<br>`media_and_timezone.test.js` | End-to-end complaint creation, status transitions, UTC timestamp preservation. |
| **Auto-Assignment & SLA** | `auto_staff_assignment.test.js`<br>`department_staff_isolation.test.js` | Workload balancing, 0-task prioritization, department boundary isolation. |
| **Geospatial & Duplicates** | `geolocation_tier.test.js`<br>`duplicate_detection_merge.test.js`<br>`angle_invariant_duplicate.test.js` | EXIF vs GPS conflict detection, 100m proximity matching, multi-angle duplicate checks. |
| **AI Integration** | `ai_department_hardening_integration.test.js`<br>`drainage_ai_production_integration.test.js`<br>`pipe_ai_production_integration.test.js` | YOLO model responses, LangGraph fallback logic, category validation. |
| **System Integrity & Audit** | `blockchain_integrity.test.js`<br>`blockchain_production_integrity.test.js`<br>`super_admin.test.js`<br>`authoritative_data_reconciliation.test.js` | SHA-256 receipt verification, super-admin console commands, profile reconciliation. |
| **Localization Audits** | `i18n_comprehensive_audit.js`<br>`scan_untranslated.js` | Verifies translation key completeness across `en`, `hi`, and `mr`. |

## Test Structure & Patterns

**Standard Suite Template (`backend/tests/[suite].test.js`):**
```javascript
const assert = require('assert');
const { query } = require('../src/config/db');

async function run() {
  console.log('--- Testing [Feature Name] ---');

  // 1. Arrange / Setup
  const testPayload = { ... };

  // 2. Act
  const result = await someServiceFunction(testPayload);

  // 3. Assert
  assert.ok(result, 'Result should be defined');
  assert.strictEqual(result.status, 'success', 'Status must be success');

  console.log('✔ [Feature Name] passed successfully.');
}

module.exports = { run };
if (require.main === module) {
  run().catch(err => {
    console.error('❌ Test failed:', err);
    process.exit(1);
  });
}
```

## Mocking & Environment Isolation

- **In-Memory SQLite**: Unit tests run against local SQLite database tables without requiring network access to cloud Supabase instances.
- **Deterministic Seed Data**: Test suites generate isolated records using unique test prefixes (e.g., `TEST-COMPLAINT-${Date.now()}`) and execute cleanup hooks.
- **Simulated JWT Tokens**: `DEMO_USER_TOKENS` in `backend/src/middleware/auth.js` provide pre-configured identities for Citizen, HOD, Field Staff, and City Admin during headless testing.
- **AI Mock Payloads**: In testing environments where the Python AI microservice is offline, `backend/src/services/aiService.js` automatically routes through predictable heuristic fallbacks to ensure test suite repeatability.

---
*Testing documentation verified against active backend test runners and test suites on 2026-10-23.*
