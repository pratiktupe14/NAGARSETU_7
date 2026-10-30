# NagarSetu 3.1 — Complaint Cleanup Audit & Pre-Execution Report

**Target Project**: `ozeiymkbxtrqqdoxtmhm`  
**Supabase Endpoint**: `https://ozeiymkbxtrqqdoxtmhm.supabase.co`  
**Deployment URL**: `https://nagarsetu-ai-ivory.vercel.app`  
**Report Date**: October 2026  
**Status**: Pre-Execution Audit Complete & Verified  

---

## 1. System Architecture & Authoritative Target Audit

### 1.1 Multi-Tier Architecture Overview
NagarSetu 3.1 operates on a hybrid architecture designed for zero-config local development and scalable cloud execution:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NAGARSETU 3.1 ECOSYSTEM                         │
├────────────────────────────────┬───────────────────────────────────────┤
│ Frontend Portals (React/Vite)  │ Municipal Admin, Dept Head, Staff     │
│ Direct Cloud Client            │ frontend/src/lib/supabase.ts           │
│ Backend Service (Express/Node) │ backend/src/app.js (REST & Vercel API)│
│ Production Database            │ Supabase PostgreSQL (ozeiymkbxtrqqdoxtmhm) │
│ Local Development Database     │ backend/nagarsetu.sqlite              │
│ Cloud File Storage             │ Supabase Storage ('issues' bucket)    │
│ Local Upload Storage           │ backend/uploads/                      │
└────────────────────────────────┴───────────────────────────────────────┘
```

### 1.2 The Authoritative Target
All three user-facing portals (Municipal Admin, Department Head, and Field Staff) load complaint data directly from **Supabase PostgreSQL** (`https://ozeiymkbxtrqqdoxtmhm.supabase.co`) using the client in `frontend/src/lib/supabase.ts`. 

The local SQLite database (`backend/nagarsetu.sqlite`) is only used when running offline development tests without environment variables configured. It currently contains **0 complaints**.

---

## 2. Root Cause: Why Complaints Displayed Despite Earlier Zero Counts

The investigation uncovered why previous deletion scripts reported success while the production admin dashboard still displayed 60 complaints:

### 2.1 The RLS "Silent Deletion Filter" Bug
In Supabase PostgreSQL, Row-Level Security (RLS) is enabled on `public.complaints` and `public.complaint_status_history`. In `supabase/master_migration.sql` (and `supabase/migrations/20260827000000_nagarsetu_master_schema.sql`):
- `Complaints select policy` (SELECT) was created.
- `Complaints insert policy` (INSERT) was created.
- `Complaints update policy` (UPDATE) was created.
- **NO `FOR DELETE` policy** was ever defined.

In PostgreSQL, when RLS is active on a table and no applicable policy grants `DELETE` permission, PostgreSQL enforces a **default-deny** rule. Instead of throwing an exception, PostgreSQL quietly filters out all candidate rows and affects 0 rows. PostgREST then returns:
```json
{
  "data": [],
  "error": null,
  "status": 200,
  "statusText": "OK"
}
```

### 2.2 The Backend Adapter Fallback Bug in `db.js`
In `backend/src/config/db.js`, the Supabase query adapter contained the following logic:
```javascript
// BEFORE (Buggy fallback)
if (upper.startsWith('DELETE FROM COMPLAINTS')) {
  const idParam = params[0];
  if (idParam) {
    const { data, error } = await supabase.from('complaints').delete().eq('id', idParam).select();
    if (!error) {
      return { rows: data || [], rowCount: (data && data.length) ? data.length : 1 };
    }
  }
}
```
When PostgREST returned `data: []` (0 rows deleted), `(data && data.length) ? data.length : 1` evaluated to **`1`**. The backend falsely reported `rowCount: 1` as if the row had been deleted!

> [!NOTE]
> **Resolution Applied**: We updated `backend/src/config/db.js` so that `rowCount` evaluates strictly to `(data && data.length) ? data.length : 0` on both `DELETE` and `UPDATE` statements.

### 2.3 Local SQLite vs Supabase Disconnect
Earlier automated verification scripts checked `backend/nagarsetu.sqlite` (which had 0 complaints) and reported "All Zero," failing to query the live Supabase PostgreSQL instance where the 60 complaints resided.

---

## 3. Database Inventory & Dependency Graph

### 3.1 Pre-Cleanup Counts in Production Supabase (`ozeiymkbxtrqqdoxtmhm`)

| Table Name | Pre-Cleanup Count | Action | Justification |
| :--- | :--- | :--- | :--- |
| **`complaints`** | **60** | **PURGE** | Authoritative complaint parent table |
| **`complaint_status_history`** | **108** | **PURGE** | Lifecycle transition log linked to complaints |
| **`task_assignments`** | **1** | **PURGE** | Staff task assignments linked to complaints |
| **`complaint_feedback`** | **0** | **PURGE** | Citizen rating & reviews for complaints |
| **`notifications`** (complaint-linked) | **0** | **PURGE** | Notifications referencing `complaint_id` |
| **`recurring_issue_links`** | **0 / Schema check** | **PURGE** | Recurring complaint links |
| **`complaint_evidence_versions`** | **0 / Schema check** | **PURGE** | Versioned complaint replacement evidence |
| **`users`** | **68** | **PRESERVE** | Citizen, staff, and admin accounts |
| **`profiles`** | **67** | **PRESERVE** | User profile identities & contact info |
| **`departments`** | **6** | **PRESERVE** | Municipal department registry (PWD, SAN, etc.) |
| **`department_heads`** | **7** | **PRESERVE** | Official leadership assignments |
| **`user_roles`** | **1** | **PRESERVE** | City Administrator role mapping |
| **`announcements`** | **0** | **PRESERVE** | Civic broadcast communications |

### 3.2 Breakdown of Existing 60 Complaints by Status
- **Submitted / New**: 41
- **In Progress**: 7
- **Staff Assigned**: 2
- **Resolved**: 1
- **Reopened**: 9
- **Total**: **60**

### 3.3 Foreign-Key Dependency Order
```
           ┌────────────────────────────┐
           │     public.complaints      │
           └──────┬──────────────┬──────┘
                  │              │
      ┌───────────┴──────────┐   │ (self-referential: duplicate_of_id)
      ▼                      ▼   ▼
complaint_status_history   task_assignments
      ▼                      ▼
complaint_feedback         notifications
      ▼                      ▼
recurring_issue_links      complaint_evidence_versions
```

To prevent constraint violations during deletion without disabling database constraints:
1. First update `duplicate_of_id = NULL` on `complaints` to break the self-referential cycle.
2. Delete all child records from dependent tables (`complaint_status_history`, `task_assignments`, etc.).
3. Delete all records from `complaints`.
4. Install missing `DELETE` policies on `complaints`, `complaint_status_history`, `task_assignments`, and `complaint_feedback` for `city_admin`, `admin`, and `super_admin`.

---

## 4. Storage & Attachment Inventory

### 4.1 Supabase Cloud Storage
- Bucket: `issues`
- Root contents: **0 objects**
- `uploads/` path contents: **0 objects**
- Result: No complaint image files exist in Supabase storage buckets.

### 4.2 Local Filesystem Uploads (`backend/uploads/`)
- Total files found: 7
- **5 Orphaned test complaint images purged**:
  - `060423ab-81c3-4f4a-a6ab-0449404db247.jpg` (deleted)
  - `0ed0346b-10e8-4009-9928-80fce15a9749.jpg` (deleted)
  - `357086b2-623f-4134-94a2-0805f8ff297c.jpg` (deleted)
  - `54653b86-1f4e-46cd-b8b2-e08acec02162.png` (deleted)
  - `59773f38-d82d-40ad-9599-57cb9160ed0a.jpg` (deleted)
- **2 Core files preserved**:
  - `civic-default.jpg` (Default fallback civic placeholder asset)
  - `test-pothole.jpg` (CI/CD test runner fixture)

---

## 5. Rollback & Recovery Strategy

1. **Transactional Safety**:
   The cleanup script runs inside a single `BEGIN; ... COMMIT;` block. If any count verification check fails or an unexpected error occurs, the entire transaction rolls back automatically with `ROLLBACK;`.
2. **PostgreSQL PITR (Point-In-Time-Recovery)**:
   Supabase PostgreSQL maintains daily WAL archives and backups. If any historical records ever need restoration, PITR is available directly via the Supabase Dashboard under Project Settings > Backups.
3. **Core Data Immutability**:
   `users`, `profiles`, `departments`, and `department_heads` are completely omitted from all `DELETE` clauses. The transaction includes an explicit assertion verifying `v_users_count > 0`, `v_depts_count > 0`, and `v_heads_count > 0`.
