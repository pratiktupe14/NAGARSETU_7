# Roadmap: NAGARSETU 3.1

## Overview

NAGARSETU 3.1 is an existing full-stack civic operations platform. Milestone 1.0 (Phases 1–6) represents the historically completed baseline covering full tri-lingual localization, multi-angle defect reporting with 3-tier geolocation, workload-balanced staff assignment, admin heatmaps, and security/reliability hardening. Milestone 1.1 (Phases 7–9) outlines proposed future enhancements covering real-time event distribution, external microservice containerization, and client-side bundle optimization.

## Milestones

- ✅ **v1.0 Core Platform & Localization** — Phases 1–6 (Completed baseline, verified in `.gsd/` and codebase audit)
- 📋 **v1.1 Operational Hardening & Realtime** — Phases 7–9 (Proposed, unapproved until validated)

## Phases

- [x] **Phase 1: Localization Foundation & Dynamic Translators** - Complete civic translation dictionaries for English, Hindi, and Marathi with dynamic status/category translators.
- [x] **Phase 2: Navigation & Shell Localization** - Navigation shell, sidebar, badge indicators, and language switcher wired to shared context.
- [x] **Phase 3: Citizen Portal** - Multi-angle photo capture, EXIF/GPS geolocation cascade, 100m proximity duplicate detection, and citizen tracking.
- [x] **Phase 4: Department Head & Staff Portals** - Workload-balanced field staff task allocation, GIS navigation maps, and resolution proof submission.
- [x] **Phase 5: City Admin & Developer Console** - Municipal oversight dashboards, overdue complaint heatmaps, announcements, and developer console.
- [x] **Phase 6: System Reliability, Security & Verification** - Dual-database runner, rate limiting, magic-byte upload validation, error hardening, and mobile responsiveness.
- [ ] **Phase 7: Realtime Notifications** - Instant real-time push notifications for field staff task assignment and citizen complaint status updates.
- [ ] **Phase 8: Secure External AI Microservice Deployment** - Production containerization (Docker) and TLS-secured hosting for the Python FastAPI computer vision service.
- [ ] **Phase 9: Language Dictionary Code-Splitting & Optimization** - Dynamic JSON chunk loading for Hindi and Marathi translation dictionaries.

## Phase Details

### Phase 1: Localization Foundation & Dynamic Translators
**Goal:** Establish comprehensive civic translation dictionaries and dynamic database value translators for `en`, `hi`, and `mr`.
**Depends on:** Initial setup
**Status:** Complete (Verified in `frontend/src/utils/i18n.ts` and `.gsd/STATE.md`)
**Success Criteria:**
  1. Complete translation dictionary exists for English, Hindi, and Marathi.
  2. Categories, statuses, priorities, and departments render in active language without altering stored database values.

### Phase 2: Navigation & Shell Localization
**Goal:** Wire persistent localization across application navigation, headers, drawers, and status indicators.
**Depends on:** Phase 1
**Status:** Complete (Verified in `Navbar.tsx`, `Sidebar.tsx`, `LanguageSelector.tsx`)
**Success Criteria:**
  1. Switching language immediately updates all shell and navigation labels.
  2. Selected language persists across page refreshes via `localStorage`.

### Phase 3: Citizen Portal
**Goal:** Enable citizens to report civic defects with multi-angle photos, verified geolocation, and duplicate detection.
**Depends on:** Phase 2
**Status:** Complete (Verified in `ReportIssuePage.tsx`, `locationService.js`, `complaint.routes.js`)
**Success Criteria:**
  1. Photos parsed for EXIF GPS with fallback to device GPS or interactive map pin-drop.
  2. Duplicates within 100 meters detected and surfaced before submission.
  3. AI defect detection pre-fills category and department fields.

### Phase 4: Department Head & Staff Portals
**Goal:** Enable department heads to manage municipal workloads and empower field staff to resolve assigned tasks.
**Depends on:** Phase 3
**Status:** Complete (Verified in `DepartmentHeadPortal.tsx`, `StaffPortal.tsx`, `autoAssignmentService.js`)
**Success Criteria:**
  1. Complaints routed to matching canonical department.
  2. Field staff automatically assigned based on workload metrics and 0-task priority.
  3. Resolution verified with before/after photos and notes.

### Phase 5: City Admin & Developer Console
**Goal:** Provide municipal leadership and system engineers with cross-departmental analytics and control.
**Depends on:** Phase 4
**Status:** Complete (Verified in `AdminPortal.tsx`, `SuperAdminConsolePage.tsx`)
**Success Criteria:**
  1. City-wide heatmap visualizes complaint density and overdue SLA breaches.
  2. Municipal announcements broadcast to citizen portals.
  3. Developer console exposes system health and data reconciliation tools.

### Phase 6: System Reliability, Security & Verification
**Goal:** Harden security, prevent data leakage, support offline local development, and verify zero regressions.
**Depends on:** Phase 5
**Status:** Complete (Verified in `backend/src/config/db.js`, `errorHandler.js`, 32 backend test suites)
**Success Criteria:**
  1. Dual-database runner connects to Supabase PostgreSQL or falls back to local SQLite cleanly.
  2. Rate limiting and magic-byte validation active on all upload and auth endpoints.
  3. Production build compiles cleanly with 0 TypeScript errors.
  4. 2-pass mobile responsive layout verified across 320px–1024px.

---

### Phase 7: Realtime Notifications (Proposed)
**Goal:** Deliver instant real-time notification alerts to field service staff upon task assignment and update citizens live when complaints change status.
**Depends on:** Phase 6
**Status:** Planned (Proposed, unapproved until validated)
**Success Criteria:**
  1. Field staff receive instant notifications without manual page refresh when new tasks are assigned.
  2. Citizens receive immediate status updates when complaints transition between Submitted, In Progress, and Resolved.
  3. Fallback gracefully to HTTP polling if WebSocket / Realtime connection drops.

### Phase 8: Secure External AI Microservice Deployment (Proposed)
**Goal:** Containerize and deploy the Python FastAPI computer vision microservice to a dedicated secure host (Render / Railway / AWS) with TLS encryption and internal authentication.
**Depends on:** Phase 6
**Status:** Planned (Proposed, unapproved until validated)
**Success Criteria:**
  1. Docker container builds and loads YOLOv8 models into memory successfully.
  2. Backend REST API communicates with deployed AI service over HTTPS with shared `X-Internal-API-Key` verification.
  3. Health and readiness probes (`/health`, `/ready`) report operational status cleanly.

### Phase 9: Language Dictionary Code-Splitting & Optimization (Proposed)
**Goal:** Split the 110 KB monolithic translation dictionary in `frontend/src/utils/i18n.ts` into lazy-loaded JSON chunks to reduce initial bundle download size.
**Depends on:** Phase 6
**Status:** Planned (Proposed, unapproved until validated)
**Success Criteria:**
  1. Initial bundle includes only English strings; Hindi (`hi.json`) and Marathi (`mr.json`) load asynchronously on demand.
  2. Zero UI layout shift or delay during language switching.
  3. Offline drafts maintain access to cached language dictionaries.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|---|---|---|---|---|
| 1. Localization Foundation | v1.0 | Historical | Complete | 2026-10-23 |
| 2. Navigation & Shell | v1.0 | Historical | Complete | 2026-10-23 |
| 3. Citizen Portal | v1.0 | Historical | Complete | 2026-10-23 |
| 4. Dept Head & Staff | v1.0 | Historical | Complete | 2026-10-23 |
| 5. City Admin & Dev Console | v1.0 | Historical | Complete | 2026-10-23 |
| 6. Reliability & Security | v1.0 | Historical | Complete | 2026-10-23 |
| 7. Realtime Notifications | v1.1 | 0/TBD | Not started | - |
| 8. AI Microservice Deployment | v1.1 | 0/TBD | Not started | - |
| 9. Dictionary Code-Splitting | v1.1 | 0/TBD | Not started | - |

---
*Roadmap established from verified codebase audit and legacy .gsd records on 2026-10-23.*
