# Codebase Concerns & Technical Debt

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1

## Technical Debt & Synchronization Risks

**1. Dual-Database Schema Drift (PostgreSQL vs. SQLite):**
- **Issue**: The application maintains two separate database initialization paths. PostgreSQL DDL is defined in `supabase/master_migration.sql`, while SQLite tables are dynamically created in `backend/src/config/db.js` via inline `CREATE TABLE` and `ALTER TABLE` statements.
- **Why**: Allows complete offline local development without requiring local Docker or PostgreSQL installations, while supporting cloud-native Supabase in production.
- **Impact**: Schema modifications (e.g., adding new columns for angle photos, audit metadata, or AI confidence scores) risk being applied to Supabase but omitted from `db.js`, causing runtime query errors in SQLite.
- **Mitigation / Safe Practice**: Whenever adding or altering columns in `supabase/migrations/`, verify and mirror the corresponding column checks in `backend/src/config/db.js` (`createTablesSqlite`).

**2. Monolithic Translation Dictionary Bundle:**
- **Issue**: `frontend/src/utils/i18n.ts` contains 1,700+ keys across English, Hindi, and Marathi embedded in a single 110 KB TypeScript module.
- **Why**: Guarantees zero-network-latency translation switches and ensures translations are available during offline draft saving.
- **Impact**: Adds ~110 KB to the initial client bundle.
- **Future Improvement**: Separate translation dictionaries into JSON files loaded dynamically via `import()` when switching languages.

## Fragile Areas & Operational Gotchas

**1. Vercel Serverless Ephemeral Filesystem:**
- **Why Fragile**: Vercel serverless execution environments are ephemeral and read-only except for `/tmp`. Local filesystem writes to `backend/uploads/` will disappear when serverless containers recycle.
- **Current Safeguard**: `backend/src/config/supabaseStorage.js` uploads complaint images directly to the Supabase Storage `issues` bucket and stores permanent public HTTPS URLs.
- **Rule for Developers**: Never rely on local file paths (`/uploads/...`) in production. Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are configured so all media streams to cloud object storage.

**2. Python AI Service Decoupling in Production:**
- **Why Fragile**: `start-dev.js` starts the Python FastAPI service on `:8000` locally. However, Vercel cannot run long-lived Python FastAPI processes.
- **Current Safeguard**: `backend/src/services/aiService.js` contains a resilient multi-tier fallback chain:
  1. Python FastAPI YOLOv8 Microservice (Primary)
  2. Google Gemini Vision API (`gemini-2.5-flash`)
  3. Rule-based heuristic civic keyword matching
- **Deployment Requirement**: In production, deploy `ai_service` to an external host (Render, Railway, or AWS ECS) and configure `PYTHON_AI_URL` and `AI_INTERNAL_API_KEY` in the Vercel backend environment.

## Security Considerations

**1. Supabase Connection Pool Limits:**
- **Risk**: Direct connection strings to Supabase (`postgres://postgres:...:5432/postgres`) will quickly exhaust PostgreSQL connection pools under serverless traffic spikes.
- **Current Mitigation**: `backend/src/config/db.js` auto-rewrites legacy template placeholders and accommodates pooler domains.
- **Recommendation**: Always utilize the Supabase Supavisor pooler connection string (port `6543` in transaction mode) in production `DATABASE_URL`.

**2. Rate Limiting on Authentication Endpoints:**
- **Risk**: Brute-force credential stuffing against `/api/auth/login` and OTP generation endpoints.
- **Current Mitigation**: `authRateLimiter` applies exponential backoff and limits failed requests per IP window.
- **Recommendation**: Ensure reverse-proxy hops (`trust proxy` setting in `app.js`) correctly forward citizen client IPs rather than proxy IP addresses.

**3. Multi-Angle Photo EXIF Ground-Truthing:**
- **Risk**: Citizen may select a file with stripped EXIF metadata (e.g. forwarded via messaging apps) or spoof GPS coordinates.
- **Current Mitigation**: 3-Tier Geolocation resolution forces interactive map pin-drop if EXIF is missing, and alerts citizen if device GPS diverges >500m from photo metadata.

---
*Concerns and technical debt documented from verified codebase mechanics on 2026-10-23.*
