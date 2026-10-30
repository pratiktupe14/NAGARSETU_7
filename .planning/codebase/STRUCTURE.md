# Codebase Structure

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1

## Directory Layout

```
NAGARSETU 3.1/
├── .agent/                  # GSD agents, workflows, skills, and CLI tools
├── .gsd/                    # Historical GSD execution records (Phases 1-6)
├── .planning/               # Modern GSD planning state and codebase reference
│   └── codebase/            # 7 canonical codebase reference documents
├── ai_service/              # Python FastAPI computer vision & Google Maps microservice
│   ├── model/               # Trained YOLOv8 weight files (.pt)
│   ├── tests/               # Python unit and integration tests
│   ├── analyzer.py          # LangGraph decision logic
│   ├── google_maps_service.py # Official Google Maps SDK integration
│   ├── main.py              # FastAPI application server entry point
│   ├── model_manager.py     # In-memory model loader and health probes
│   └── requirements.txt     # Python dependencies
├── api/                     # Vercel serverless function entry points
│   └── index.js             # Serverless bridge wrapping backend/src/app.js
├── backend/                 # Node.js/Express REST API application
│   ├── src/                 # Server source code
│   │   ├── config/          # Database runner (db.js) & Supabase storage config
│   │   ├── middleware/      # Auth, rate limiting, upload handling, error handler
│   │   ├── routes/          # REST route definitions (complaint, auth, admin, etc.)
│   │   ├── schemas/         # Joi input validation schemas
│   │   ├── scripts/         # Lifecycle tests, audit scripts, and seeders
│   │   ├── services/        # Business logic (auto-assignment, AI, location)
│   │   ├── app.js           # Express app instance and middleware wiring
│   │   └── server.js        # Server bootstrapper, port binding, and seeders
│   ├── tests/               # 32 backend automated test suites and test runner
│   └── package.json         # Backend dependencies and test scripts
├── frontend/                # React 18 + TypeScript + Vite frontend
│   ├── public/              # Static assets and icons
│   ├── src/                 # Application source code
│   │   ├── components/      # Shared UI widgets, badges, layouts, maps
│   │   ├── config/          # Centralized API and environment resolver
│   │   ├── context/         # AuthContext, LanguageContext, NotificationContext
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Supabase client instantiation and helpers
│   │   ├── pages/           # Portal-specific page components
│   │   │   ├── admin/       # City Admin pages
│   │   │   ├── citizen/     # Citizen reporting, tracking, and profile pages
│   │   │   ├── departmentHead/ # HOD workload and delegation pages
│   │   │   ├── developer/   # Super Admin developer console
│   │   │   └── staff/       # Field staff task list and map pages
│   │   ├── services/        # Frontend API client service modules
│   │   ├── types/           # TypeScript database and domain interfaces
│   │   ├── utils/           # i18n translation dictionary and formatters
│   │   ├── App.tsx          # Root routing and Suspense layout boundaries
│   │   └── main.tsx         # React DOM mounting entrypoint
│   ├── index.html           # HTML template shell
│   ├── package.json         # Frontend dependencies and Vite scripts
│   ├── tailwind.config.js   # Tailwind styling configuration
│   └── vite.config.ts       # Vite bundling and chunking config
├── supabase/                # PostgreSQL schemas, migrations, and DDL
│   ├── migrations/          # Versioned SQL migration scripts
│   └── master_migration.sql # Comprehensive master schema DDL
├── package.json             # Root workspace package.json
├── start-dev.js             # Unified development bootstrapper
└── vercel.json              # Vercel deployment routing specification
```

## Directory Purposes

### `frontend/src/`
- **Purpose**: Houses the entire user interface and client-side logic.
- **Key Subdirectories**:
  - `pages/`: Grouped by user persona (`citizen`, `departmentHead`, `staff`, `admin`, `developer`). Contains top-level route views.
  - `components/`: Modular widgets including `StatusBadge.tsx`, `PriorityBadge.tsx`, `LanguageSelector.tsx`, `LeafletMap.tsx`, `DashboardLayout.tsx`.
  - `context/`: Cross-cutting application state (`AuthContext.tsx`, `LanguageContext.tsx`, `NotificationContext.tsx`).
  - `services/`: Axios/Fetch clients communicating with backend endpoints (`complaintService.ts`, `adminService.ts`, `departmentService.ts`, `aiVisionService.ts`).
  - `utils/`: Localization core (`i18n.ts`) providing 1,700+ translation keys and dynamic translators.

### `backend/src/`
- **Purpose**: Central business logic, database queries, and secure API endpoints.
- **Key Subdirectories**:
  - `routes/`: Modular Express route routers (`auth.routes.js`, `complaint.routes.js`, `admin.routes.js`, `department.routes.js`, `staff.routes.js`, `ai.routes.js`).
  - `services/`: Encapsulated domain logic (`autoAssignmentService.js`, `locationService.js`, `aiService.js`, `recurringIssueService.js`).
  - `config/`: Database client setup with Postgres-to-SQLite fallback (`db.js`) and Supabase Storage integration (`supabaseStorage.js`).
  - `middleware/`: JWT verification (`auth.js`), rate limiting (`rateLimiter.js`), and schema validation (`validateInput.js`).

### `ai_service/`
- **Purpose**: High-performance Python microservice for deep-learning computer vision and GIS boundary logic.
- **Key Files**:
  - `main.py`: ASGI server exposing `/analyze` and `/google-maps/*`.
  - `model_manager.py`: Loads YOLOv8 models into memory during FastAPI lifespan.
  - `analyzer.py`: LangGraph state machine coordinating defect severity and bounding boxes.

### `supabase/`
- **Purpose**: Authoritative PostgreSQL schema specifications and database migrations.
- **Key Files**:
  - `master_migration.sql`: Comprehensive database definition (tables, enums, triggers, RLS policies, seed departments).
  - `migrations/20260827000000_nagarsetu_master_schema.sql`: Versioned master migration.

## Key File Locations

**Entry Points:**
- Unified Dev: `start-dev.js`
- Frontend: `frontend/src/main.tsx` & `frontend/index.html`
- Backend API: `backend/src/server.js` (Express listener) & `backend/src/app.js` (App configuration)
- Serverless API: `api/index.js` (Vercel bridge)
- AI Service: `ai_service/main.py`

**Configuration:**
- Root Environment: `.env.example`, `.env.local`
- Backend Database: `backend/src/config/db.js`
- Frontend API Resolver: `frontend/src/config/apiConfig.ts`
- Build Configurations: `frontend/vite.config.ts`, `frontend/tsconfig.json`, `vercel.json`

**Testing:**
- Backend Test Harness: `backend/tests/run_tests.js`
- Test Suites: `backend/tests/*.test.js`
- Python AI Tests: `ai_service/tests/test_*.py`

## Naming Conventions

**Frontend (`frontend/src`):**
- Components and Pages: `PascalCase.tsx` (e.g., `ReportIssuePage.tsx`, `StatusBadge.tsx`).
- Services and Utilities: `camelCase.ts` (e.g., `complaintService.ts`, `apiConfig.ts`, `i18n.ts`).
- Types and Interfaces: `camelCase.types.ts` or `PascalCase` inside type definitions (e.g., `database.types.ts`).

**Backend (`backend/src`):**
- Route Files: `[domain].routes.js` (e.g., `complaint.routes.js`, `auth.routes.js`).
- Service Files: `[domain]Service.js` (e.g., `autoAssignmentService.js`, `locationService.js`).
- Middleware Files: `camelCase.js` (e.g., `auth.js`, `rateLimiter.js`, `validateInput.js`).
- Test Files: `snake_case.test.js` (e.g., `auto_staff_assignment.test.js`, `security_and_fixes.test.js`).

**AI Service (`ai_service`):**
- Modules: `snake_case.py` (e.g., `model_manager.py`, `google_maps_service.py`).
- Test Files: `test_snake_case.py` (e.g., `test_pipe_ai.py`).

## Where to Add New Code

**Adding a New Civic Category / Department:**
1. Database: Update `supabase/master_migration.sql` (insert into `departments` table).
2. Backend Constants: Add to `CANONICAL_DEPARTMENTS` in `backend/src/services/autoAssignmentService.js` and `CATEGORY_DEPARTMENT_MAP` in `backend/src/services/aiService.js`.
3. Frontend Constants: Add to `frontend/src/types/database.types.ts` and `frontend/src/services/departmentService.ts`.
4. Localization: Add corresponding keys to `frontend/src/utils/i18n.ts` under `en`, `hi`, and `mr`.

**Adding a New API Route:**
1. Route Definition: Add to `backend/src/routes/[domain].routes.js`.
2. Input Validation: Define Joi schema in `backend/src/schemas/[domain].schemas.js`.
3. Mount Route: Ensure mounted with appropriate rate limiter in `backend/src/app.js`.
4. Automated Test: Add test cases to `backend/tests/[domain].test.js`.

**Adding a New Frontend Portal Page:**
1. Page Component: Create `frontend/src/pages/[role]/[PageName]Page.tsx`.
2. Routing: Register lazy-loaded route in `frontend/src/App.tsx` wrapped in `ProtectedRoute`.
3. Navigation Link: Add entry to `DashboardLayout.tsx` or sidebar navigation.
4. UI Localization: Ensure all headings, labels, and table headers use `t('key')` from `useLanguage()`.

---
*Structure documentation verified against physical repository layout on 2026-10-23.*
