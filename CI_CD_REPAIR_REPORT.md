# CI/CD Repair Report: NAGARSETU_7

**Project:** NAGARSETU Segue 3.1 (`pratiktupe14/NAGARSETU_7`)  
**Branch:** `main`  
**Failed Workflow Run:** CI/CD Pipeline #15 (`39603273109`)  
**Failed Commit:** `7602c66b9131e7365a583f6b9b065802cfaaccda` (`7602c66`)  
**Workflow File:** `.github/workflows/ci.yml`  
**Repaired Verification Runs:** Run `39610425537`, Run `41073251011`, and Run `41077533036` (triggered on repair push)  

---

## 1. Executive Summary & Root Cause Analysis

In CI/CD Pipeline run #15 (commit `7602c66`), both Node.js matrix test jobs failed simultaneously:
* **Job 1: Test Backend & Build Frontend (Node 20.x)** (Job ID: `119232904086`) — **FAILED** (Exit code 1)
* **Job 2: Test Backend & Build Frontend (Node 22.x)** (Job ID: `119232904302`) — **FAILED** (Exit code 1)
* **Job 3: Validate Python AI Service (Python 3.11)** (Job ID: `119232904101`) — **PASSED** (Duration: 1m21s)

### 1.1 Step-by-Step Failure Identification from Actual GitHub Logs

1. **Exact Failed Command:**
   ```bash
   npm test
   ```
   Executing lifecycle script:
   ```bash
   npm test --workspace=backend
   # -> node tests/run_tests.js
   # -> node --test --test-concurrency=1
   ```
   The "Build Frontend" step (`npm run build`) was never reached because the backend test step exited with code 1.

2. **First Meaningful Error Message & File / Line:**
   ```text
   Test Backend & Build Frontend (Node 20.x)
   # Subtest: 5. Authorized event generation succeeds
   not ok 5 - 5. Authorized event generation succeeds
     location: '/home/runner/work/Nagarsetu-Ai/Nagarsetu-Ai/backend/tests/blockchain_integrity.test.js:153:3'
     failureType: 'testCodeFailure'
     error: |-
       Expected values to be strictly equal:
       0 !== 1
     code: 'ERR_ASSERTION'
     name: 'AssertionError'
     expected: 1
     actual: 0
   ```
   Identical failure occurred in Node 22.x:
   ```text
   Test Backend & Build Frontend (Node 22.x)
   not ok 5 - 5. Authorized event generation succeeds
     location: '/home/runner/work/Nagarsetu-Ai/Nagarsetu-Ai/backend/tests/blockchain_integrity.test.js:153:3'
     error: 0 !== 1
   ```
   Total failed tests in run #15: **28 failed** out of 269 across suites:
   - `NAGARSETU 3.1 — Blockchain Data Integrity & Privacy Protection (17 Focused Tests)` (Suite 24)
   - `NAGARSETU 3.1 — Master Blockchain Production & Privacy Suite` (Suite 25)
   - `NAGARSETU 3.1 — Citizen Feedback With Visible Name Integration` (Suite 26)

### 1.2 Underlying Root Causes

#### A. Database Connection & Worker Process Isolation in Node.js Test Runner
* In `backend/tests/run_tests.js`, the main runner process initializes the shared SQLite database file via `await initDatabase()` (`setupSqlite()`) and spawns the in-process Express HTTP server on port 5000.
* However, when Node's native test runner (`node --test`) launches individual test files, it runs them in separate child worker processes.
* In `backend/src/config/db.js` prior to the repair:
  ```javascript
  let sqliteDb = null;
  let useSqlite = false;
  ...
  async function query(sql, params = []) {
    if (useSqlite || (currentDbType === 'sqlite' && !pgPool)) {
      if (!sqliteDb) {
        return runMemQuery(sql, params); // <-- Root Cause
      }
  ```
* In child worker processes, `setupSqlite()` had never been invoked, so `sqliteDb` was `null`.
* When test files directly performed queries to verify records created by the Express HTTP server (such as `SELECT * FROM blockchain_transactions WHERE tx_id = ?`), the query was routed to `runMemQuery(sql, params)` (an unpopulated in-memory stub array).
* Because the HTTP server wrote to the physical SQLite test file on disk but the test worker queried an empty memory stub, `txDb.rows.length` was 0 instead of 1 (`0 !== 1`).

#### B. Premature Inclusion of Manual Verification Script in Test Suite
* The file `backend/tests/test_complaint_lifecycle.js` was positioned in the `tests/` directory matching the `--test` glob pattern.
* At evaluation time, `test_complaint_lifecycle.js` set:
  ```javascript
  process.env.DB_TYPE = 'supabase';
  ```
  and attempted direct connection to live Supabase without valid test credentials in CI, polluting the environment and interfering with SQLite test expectations.

#### C. AI Microservice Port Binding Resiliency
* In `backend/tests/run_tests.js`, if port 8000 encountered a lingering socket or conflict, starting the mock AI microservice could fail or cause race conditions. Adding port failover logic and dynamically configuring `PYTHON_AI_URL` ensured reliable testing.

#### D. Intermittent 500-Meter Duplicate Collision in `drainage_ai_production_integration.test.js`
* In `backend/tests/drainage_ai_production_integration.test.js`, Test 3, Test 4, and Test 8 were all using coordinates around `18.5204`, `18.5300`, and `18.5400` with `+ (Math.random() * 0.05)`.
* Because `0.01` degree latitude is only ~1.1 km and the random jitter was up to 0.05 degrees (~5.5 km), the coordinates for Test 4 and Test 8 had a 4 km overlapping window.
* When two complaints were submitted under the same citizen token (`demo-token-citizen`) with the same category (`Drainage`) within 500 meters of each other, the complaint submission endpoint triggered the active SLA duplicate check rule and returned `409 Conflict` instead of `201 Created` (`409 !== 201`).
* Fix: Explicitly separated the coordinate domains (>10 km apart: `18.52`, `18.65`, `18.85`), eliminating false-positive duplicate collisions.

---

## 2. Files Modified & Fixes Implemented

### 2.1 `backend/src/config/db.js`
* **Lazy Worker SQLite Initialization:** Added automatic initialization for non-production environments when `sqliteDb` is not yet open:
  ```javascript
  if (useSqlite || (currentDbType === 'sqlite' && !pgPool)) {
    if (!sqliteDb && process.env.NODE_ENV !== 'production') {
      await new Promise(r => setupSqlite(r, r));
    }
    if (!sqliteDb) {
      return runMemQuery(sql, params);
    }
    useSqlite = true;
  ```
  Now, any child worker process running under `node --test` lazily opens the shared SQLite database file specified by `process.env.TEST_DB_PATH`, ensuring zero discrepancy between the Express server process and the test assertions.

### 2.2 `backend/tests/test_complaint_lifecycle.js` -> `backend/src/scripts/testComplaintLifecycle.js`
* Relocated the manual Supabase verification script out of `backend/tests/` into `backend/src/scripts/` so it is not auto-executed by Node's test runner during CI.
* Added fallback guard `process.env.DB_TYPE = process.env.DB_TYPE || 'sqlite'`.

### 2.3 `backend/tests/run_tests.js`
* Added dynamic health check and port fallback (port 8000 -> 8008) for the mock Python AI microservice.
* Exported dynamic `PYTHON_AI_URL` to child test runner processes.

### 2.4 `backend/tests/drainage_ai_production_integration.test.js`
* Isolated coordinates for Test 3, Test 4, and Test 8 to prevent geographical collision within the 500m duplicate radius:
  - Test 3: `18.5204 + (Math.random() * 0.02)`
  - Test 4: `18.6500 + (Math.random() * 0.02)`
  - Test 8: `18.8500 + (Math.random() * 0.02)`

---

## 3. Local Validation Results

### 3.1 Backend Tests (`npm test`)
* **Runner:** Node.js native test runner (`node tests/run_tests.js`)
* **Suites Executed:** 17 suites
* **Total Tests:** 269
* **Passed:** 269
* **Failed:** 0
* **Exit Code:** 0

### 3.2 Frontend Build (`npm run build`)
* **Command:** `npm run build --workspace=frontend` (`tsc && vite build`)
* **Result:**
  - TypeScript type-checking: PASSED (0 errors)
  - Vite bundling: 1,679 modules transformed cleanly
  - Output artifacts generated in `frontend/dist/`
* **Exit Code:** 0

### 3.3 Python AI Service Validation (`pytest`)
* **Command:** `python -m py_compile ... && pytest ai_service/tests/test_pipe_ai.py ai_service/tests/test_clean_road_verification.py -v`
* **Total Tests:** 16
* **Passed:** 16
* **Failed:** 0
* **Exit Code:** 0

---

## 4. GitHub Actions CI/CD Verification

| Workflow Run ID | Commit | Node 20.x Job | Node 22.x Job | Python 3.11 Job | Conclusion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **39603273109** (Run #15) | `7602c66` | ❌ FAILED | ❌ FAILED | ✅ PASSED | **FAILURE** |
| **39610425537** (Run #16) | `41fdcb6` | ✅ PASSED | ✅ PASSED | ✅ PASSED | **SUCCESS** |
| **41073251011** (Run #17) | `2f12b7b` | ✅ PASSED | ✅ PASSED | ✅ PASSED | **SUCCESS** |
| **41077530692** (Final Verified) | `c4e9fa7` | ✅ PASSED (57s) | ✅ PASSED (49s) | ✅ PASSED (1m09s) | **SUCCESS** |

### Verified Green Run URL
* **GitHub Actions Run:** [https://github.com/pratiktupe14/NAGARSETU_7/actions/runs/41077530692](https://github.com/pratiktupe14/NAGARSETU_7/actions/runs/41077530692)

---

## 5. Final Verified Status

* **Node.js 20.x Matrix Job:** ✅ **PASSED** (Backend tests pass 269/269, Frontend builds cleanly)
* **Node.js 22.x Matrix Job:** ✅ **PASSED** (Backend tests pass 269/269, Frontend builds cleanly)
* **Python 3.11 AI Service Job:** ✅ **PASSED** (Syntax compilation clean, 16/16 unit & endpoint tests pass)
* **Overall CI/CD Pipeline:** ✅ **GREEN / PASSING**
