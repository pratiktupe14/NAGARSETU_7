# External Integrations

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1

## External APIs & Microservices

**Python AI Computer Vision Service (Internal):**
- **Purpose**: Local deep-learning inference pipeline for defect classification, bounding box detection, and department routing.
- **Service Location**: `ai_service/main.py` running on port 8000 (configurable via `AI_PORT` or `PORT`).
- **Integration Client**: Native Node.js `fetch` / `FormData` in `backend/src/services/aiService.js` (`callLocalAiService`).
- **Authentication**: Shared secret header (`X-Internal-API-Key`) matching `AI_INTERNAL_API_KEY` / `INTERNAL_AI_SECRET`.
- **Endpoints**:
  - `POST /analyze` & `POST /analyze-complaint-image`: Multipart image upload with optional `domain` hint (`road`, `waste`, `pipe`, `drainage`).
  - `GET /health` & `GET /ready`: Health check and readiness probe verifying all 4 YOLO models (`civicmodel`, `wasteModel`, `waterPipeModel`, `drainageModel`).

**Google Maps Platform:**
- **Purpose**: Geocoding addresses, reverse geocoding GPS coordinates, computing driving navigation directions, and validating Nashik municipal jurisdiction.
- **SDK/Integration**:
  - Python: `google_maps_service.py` in `ai_service` invoking official Google Maps REST API.
  - Node.js: `backend/src/routes/maps.routes.js` providing authenticated proxy endpoints.
  - Frontend: `@vis.gl/react-google-maps` and standard Leaflet tiles.
- **Authentication**: `GOOGLE_MAPS_API_KEY` (backend/AI) and `VITE_GOOGLE_MAPS_API_KEY` (frontend).

**Google Gemini Vision (Fallback Cloud AI):**
- **Purpose**: Cloud-based computer vision fallback when local YOLOv8 models are unreachable or operating in minimal resource environments.
- **Client**: REST invocation in `backend/src/services/aiService.js`.
- **Auth**: `GEMINI_API_KEY` or `GOOGLE_AI_KEY` environment variable.
- **Model**: `gemini-2.5-flash` with structured JSON prompt enforcement.

## Data Storage & Databases

**Primary Database (Production): Supabase PostgreSQL**
- **Provider**: Supabase Cloud (AWS ap-southeast-1 pooler or direct PostgreSQL).
- **Client**: `pg` Pool in `backend/src/config/db.js` and `@supabase/supabase-js`.
- **Connection**: `DATABASE_URL` / `SUPABASE_DB_URL` with SSL support (`ssl: { rejectUnauthorized: false }`).
- **Migrations**: SQL migration scripts in `supabase/master_migration.sql` and `supabase/migrations/20260827000000_nagarsetu_master_schema.sql`.

**Fallback Database (Local Development): SQLite**
- **Engine**: `sqlite3` embedded file database.
- **Location**: `backend/src/database.sqlite` (or `backend/nagarsetu.sqlite`).
- **Activation**: Automatically activated when `DB_TYPE=sqlite` or when PostgreSQL pool fails during development initialization.

**Object & Media Storage:**
- **Provider**: Supabase Storage.
- **Bucket**: `issues` bucket.
- **Implementation**: `backend/src/config/supabaseStorage.js` (`uploadBufferToSupabase`).
- **Public URL Resolution**: `supabase.storage.from('issues').getPublicUrl(filePath)`.
- **Local Fallback**: Ephemeral local uploads served from `backend/uploads/` (local) or `/tmp/uploads` (serverless).

## Authentication & Identity

**Custom JWT RBAC Engine:**
- **Implementation**: `jsonwebtoken` and `bcryptjs` in `backend/src/middleware/auth.js`.
- **Token Format**: Bearer JWT containing `id`, `name`, `mobile`, `email`, `role`, `department_id`, and `language_pref`.
- **Expiration**: 8 hours (`expiresIn: '8h'`).
- **Client Storage**: `sessionStorage` and `localStorage` under `nagarsetu_token` and `nagarsetu_user`.
- **Roles Enforced**: `citizen`, `department_head`, `service_staff`, `city_admin`, `super_admin`.

**Supabase Auth Interoperability:**
- Authenticated middleware checks both custom JWT signatures and Supabase session tokens via `supabase.auth.getUser()`, allowing unified citizen onboarding across OAuth and mobile OTP.

## Hosting & Deployment Architecture

**Frontend & API Gateway:**
- **Platform**: Vercel.
- **Configuration**: `vercel.json` routing all `/api/(.*)` requests to serverless execution in `api/index.js`, while serving SPA routes through Vite static artifacts.
- **CORS Handling**: Dynamic origin resolution in `backend/src/app.js` authorizing official production origins (`https://nagarsetu-ai.vercel.app`, `https://nagarsetu-ai-pi.vercel.app`), local development ports (`3000`, `5173`, `4173`), and Vercel preview URLs.

**AI Microservice:**
- **Platform**: Standalone Docker container or persistent Python host (local `python main.py` or cloud VM) communicating with the Express API over secure HTTP.

## Environment Variables Reference

**Critical Required Variables:**
- `DATABASE_URL`: PostgreSQL connection string (Supabase).
- `JWT_SECRET`: Secret key for signing authorization tokens (min 32 chars in production).
- `SUPABASE_URL` / `VITE_SUPABASE_URL`: Supabase project URL (`https://<project-ref>.supabase.co`).
- `SUPABASE_ANON_KEY` / `VITE_SUPABASE_ANON_KEY`: Supabase client anonymous API key.
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase administrative key for backend storage uploads and schema queries.
- `AI_INTERNAL_API_KEY`: Secret token authenticating Express to Python AI microservice requests.
- `PYTHON_AI_URL`: Microservice endpoint (default `http://localhost:8000/analyze`).
- `GOOGLE_MAPS_API_KEY`: Google Cloud API key for Geocoding and Directions APIs.

---
*Integrations analysis verified against active backend services and client libraries on 2026-10-23.*
