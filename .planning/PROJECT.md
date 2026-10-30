# NAGARSETU 3.1 — AI-Powered Civic Operations Platform

## What This Is

NAGARSETU 3.1 is an existing full-stack civic issue reporting and municipal operations platform. It connects citizens, department heads, field service staff, and city administrators into a unified digital ecosystem. The system features multi-angle defect photo submission with 3-tier geolocation (EXIF GPS -> real-time GPS -> interactive map pin), automated computer vision defect classification (Ultralytics YOLOv8 + LangGraph), workload-balanced task assignment, and comprehensive tri-lingual localization across English, Hindi, and Marathi.

## Core Value

Reliable, verifiable civic defect reporting and equitable municipal task resolution with multi-lingual transparency, strict department isolation, and zero-loss offline resiliency.

## Requirements

### Validated

<!-- Historically completed and verified according to .gsd/ and the codebase audit -->

- ✓ **Phase 1: Localization Foundation & Dynamic Translators** — Tri-lingual civic dictionary (1,708 lines) in `frontend/src/utils/i18n.ts` supporting `en`, `hi`, and `mr` with dynamic translators for categories, priorities, statuses, and departments.
- ✓ **Phase 2: Navigation & Shell Localization** — `Navbar`, `Sidebar`, `LanguageSelector`, and badge components wired to `LanguageContext`.
- ✓ **Phase 3: Citizen Portal** — Multi-angle photo capture (`front`, `left`, `right`, `closeup`), EXIF coordinate extraction (`exifr`), 100m proximity duplicate detection, issue tracking, and nearby civic map.
- ✓ **Phase 4: Department Head & Staff Portals** — Department workload visibility, automated workload-balanced field staff assignment engine (`autoAssignmentService.js`), GIS task navigation maps, and before/after resolution evidence uploads.
- ✓ **Phase 5: City Admin & Developer Console** — Municipal oversight, overdue complaint heatmaps, city-wide announcements, and developer system audit consoles.
- ✓ **Phase 6: System Reliability, Security & Verification** — Dual-database query runner (PostgreSQL on Supabase with automatic SQLite local fallback in `backend/src/config/db.js`), exponential backoff rate limiting, magic-byte image validation, CSP nosniff headers, centralized error handler with zero information leakage, 2-pass mobile responsiveness (320px–1024px), and 32 passing automated backend test suites.

### Active (Proposed — Unapproved Until Validated)

<!-- Proposed future milestone work. Must be planned and verified before execution -->

- [ ] **Phase 7: Realtime Notifications** — WebSocket or Supabase Realtime channel integration delivering instant task dispatch alerts to field staff and real-time status progression notifications to citizens.
- [ ] **Phase 8: Secure External AI Microservice Deployment** — Production containerization (Docker) and TLS-secured deployment for the Python FastAPI computer vision microservice with internal secret rotation.
- [ ] **Phase 9: Language Dictionary Code-Splitting & Optimization** — Dynamic JSON chunk loading for Hindi (`hi.json`) and Marathi (`mr.json`) dictionaries to reduce initial client bundle weight.

### Out of Scope

- **Framework Rewrite to Next.js**: The decoupled React 18 + Vite SPA and Node/Express REST API architecture is mature, fully tested, and verified across serverless and container topologies.
- **Modifying the 7 Canonical Municipal Departments**: `PWD`, `SAN`, `WTR`, `DRN`, `ELE`, `TRF`, and `MNT` have fixed UUIDs and category mappings across the frontend, backend, AI microservice, and Supabase migrations.
- **Removing Local SQLite Fallback**: SQLite support in `backend/src/config/db.js` is essential for zero-network developer onboarding and offline test suites.

## Context & Architecture

- **Primary Architectural Reference**: Comprehensive documentation is maintained in [`.planning/codebase/`](file:///d:/NAGARSETU/NAGARSETU%203.1/.planning/codebase) (`STACK.md`, `INTEGRATIONS.md`, `ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `CONCERNS.md`).
- **Historical Milestones**: Completed execution records and historical audit journals are preserved in [`.gsd/`](file:///d:/NAGARSETU/NAGARSETU%203.1/.gsd) (`STATE.md`, `ROADMAP.md`, `SPEC.md`, `DECISIONS.md`, `JOURNAL.md`).

## Constraints

- **Tech Stack**: React 18, TypeScript 5, Vite 5, TailwindCSS 3, Express 4, Python 3.10+, FastAPI, Supabase PostgreSQL & Storage.
- **Database Safety**: Never execute destructive SQL drops or migrations on production Supabase schemas without explicit user consent.
- **Serverless Compatibility**: Media must stream to Supabase Storage (`supabaseStorage.js`); do not rely on local disk writes in production Vercel serverless environments.

## Key Decisions

| Decision | Rationale | Outcome |
| :--- | :--- | :--- |
| **Dual Database Support (PostgreSQL / SQLite)** | Enables cloud production on Supabase while allowing zero-configuration offline development via SQLite. | ✓ Good — Verified in `backend/src/config/db.js`. |
| **In-Memory Storage for Uploads with Magic Byte Inspection** | Vercel serverless environments have read-only filesystems. Memory buffers validated with magic bytes prevent MIME spoofing. | ✓ Good — Verified in Multer upload middleware. |
| **Rollup Vendor Chunk Splitting** | Initial bundle exceeded 1.8 MB. Heavy libraries (Leaflet, Chart.js, Lucide) split into dedicated chunks in `vite.config.ts`. | ✓ Good — Verified in production builds. |
| **Decoupled Python AI Microservice** | Computer vision requires heavy deep-learning dependencies (PyTorch, YOLOv8) unsuitable for standard Node.js serverless functions. | ✓ Good — Microservice communicates via REST with shared API key. |

---
*Last updated: 2026-10-23 — Baseline established from codebase audit and legacy .gsd records.*
