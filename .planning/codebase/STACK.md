# Technology Stack

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1 (Civic Issue Reporting & Municipal Operations Ecosystem)

## Languages

**Primary:**
- **TypeScript 5.2.2**: Frontend single-page application, pages, UI components, context providers, API client services, and database contract types (`frontend/src/**/*.ts`, `frontend/src/**/*.tsx`).
- **JavaScript (CommonJS)**: Express REST API server, routing controllers, middleware, business services, database query layers, test runners, and diagnostic scripts (`backend/src/**/*.js`, `backend/tests/**/*.js`).
- **Python 3.10+**: FastAPI AI microservice, Ultralytics YOLOv8 inference and training pipelines, LangGraph civic defect workflows, and Google Maps boundary services (`ai_service/**/*.py`).

**Secondary:**
- **SQL (PostgreSQL 15+ / SQLite 3)**: PostgreSQL DDL migrations and extensions for Supabase (`supabase/master_migration.sql`, `supabase/migrations/`) with dynamic fallback SQLite schemas for local development (`backend/src/config/db.js`).
- **HTML5 & CSS3 / PostCSS**: HTML application shell, Tailwind CSS directives, and responsive layouts (`frontend/index.html`, `frontend/src/index.css`).

## Runtime

**Environment:**
- **Node.js**: v18.x / v20.x LTS.
- **Python**: 3.10 - 3.12 (virtualenv recommended under `ai_service/venv` or `ai_service/.venv`).
- **Browser Runtime**: Modern evergreen browsers supporting ES2020+, Web Workers, Geolocation API, and Canvas.

**Package Manager:**
- **npm**: v10.x.
- **Monorepo Workspaces**: Root `package.json` configures npm workspaces for `["backend", "frontend"]`.
- **Lockfile**: Root `package-lock.json` present and authoritative.
- **Python Package Management**: `ai_service/requirements.txt` with pinned minimums (`pyproject.toml` also present).

## Frameworks

**Core:**
- **React 18.2.0**: Component-based UI library with hooks, context providers, suspense boundaries, and portals.
- **Vite 5.2.0**: Frontend development server and production bundle orchestrator (`@vitejs/plugin-react` 4.2.1).
- **React Router DOM 6.30.6**: Declarative client-side routing with nested layouts and role-based route guards.
- **Express 4.19.2**: Backend HTTP application server, routing pipelines, and JSON APIs.
- **FastAPI >=0.100.0 & Uvicorn >=0.22.0**: Asynchronous Python microservice framework running on ASGI server.
- **LangGraph >=0.2.0**: State graph workflow engine managing civic defect classification pipelines.
- **Ultralytics YOLOv8 >=8.0.0 & PyTorch >=2.0.0**: Deep learning computer vision models running local object detection and defect classification.

**Styling & UI:**
- **Tailwind CSS 3.4.3**: Utility-first styling engine with PostCSS 8.4.38 and Autoprefixer 10.4.19.
- **Lucide React 0.368.0**: Lightweight SVG icons.
- **Chart.js 4.4.2 & react-chartjs-2 5.2.0**: Department workload, SLA resolution, and citizen feedback charts.
- **Leaflet 1.9.4 & react-leaflet 4.2.1**: Interactive open-source maps for coordinate pin drops, issue heatmaps, and staff routes.
- **@vis.gl/react-google-maps 1.10.1**: Official Google Maps React wrapper for geocoding and live road mapping.

**Testing:**
- **Custom Node.js Test Harness**: High-speed zero-dependency test runner in `backend/tests/run_tests.js` executing 32 automated test suites.
- **Pytest**: Python test execution for AI service nodes and graph pipelines in `ai_service/tests/`.

## Key Dependencies

**Critical:**
- `@supabase/supabase-js` (Frontend `^2.112.3`, Backend `^2.112.4`): Supabase PostgreSQL client, Storage bucket uploads, Realtime subscriptions, and auth sync.
- `pg` `^8.11.5`: PostgreSQL connection pooling for production database connectivity.
- `sqlite3` `^6.0.1`: Embedded fallback database engine for offline local development.
- `jsonwebtoken` `^9.0.2` & `bcryptjs` `^2.4.3`: Stateless JWT issuance and Argon/bcrypt password hashing.
- `multer` `^1.4.5-lts.1`: Multipart form-data handling configured with `memoryStorage` for serverless compatibility.
- `exifr` `^7.1.3`: Pure-JS metadata parser extracting EXIF GPS coordinates, camera timestamp, and orientation from citizen photos.
- `joi` `^18.2.5`: Schema validation engine validating API payloads before reaching controllers.
- `express-rate-limit` `^8.6.2`: Request rate limiting with exponential backoff on auth endpoints.

## Configuration

**Environment:**
- Root `.env`, `.env.example`, `.env.local`, `.env.vercel`.
- Backend `.env` (Database URLs, JWT secret, Supabase service keys, AI service URL).
- Frontend `.env` / `import.meta.env` (Vite variables: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_GOOGLE_MAPS_API_KEY`).
- AI Service `.env` (Port, CORS origins, Google Maps API key, Internal AI secret).

**Build & Tooling:**
- `frontend/vite.config.ts`: Vite build configuration with Rollup chunk splitting (`manualChunks`).
- `frontend/tsconfig.json`: TypeScript compiler options with strict type checking.
- `start-dev.js`: Unified orchestration script booting AI service (:8000), Express backend (:5000), and Vite frontend (:3000) concurrently.

## Platform Requirements

**Development:**
- Windows 10/11, macOS, or Linux.
- Node.js 18+ and Python 3.10+ installed.
- SQLite enabled locally (no Docker required for offline local dev).

**Production Target:**
- **Frontend & REST API**: Vercel Serverless (configured via `vercel.json` routing `/api/(.*)` to `api/index.js` and serving Vite static assets).
- **Database & Object Storage**: Supabase Managed Cloud (PostgreSQL 15+ with `uuid-ossp` and `issues` storage bucket).
- **AI Microservice**: Container or dedicated VM (Docker container running `ai_service/main.py` with GPU/CPU PyTorch execution).

---
*Stack analysis verified from package.json, requirements.txt, and source configurations on 2026-10-23.*
