# Architecture

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1

## Pattern Overview

**Overall Architecture:**
NAGARSETU is a full-stack, decoupled municipal operations platform composed of three primary operational tiers:
1. **Frontend Client**: Modern React single-page application (SPA) with role-segmented workspaces and tri-lingual localization.
2. **REST API Server**: Node.js/Express backend handling authentication, complaint lifecycle workflows, automated task assignment, and database abstraction.
3. **AI Vision Microservice**: Python/FastAPI microservice executing Ultralytics YOLOv8 object detection, LangGraph decision trees, and Google Maps geocoding.

**Key Characteristics:**
- **Role-Based Workplace Isolation**: Distinct, dedicated dashboard environments for Citizens, Department Heads, Field Service Staff, City Administrators, and Super Administrators.
- **Dual-Database Resiliency**: Transparent query runner supporting Supabase PostgreSQL in production and local SQLite for offline development.
- **3-Tier Geolocation Ground-Truthing**: Priority cascade resolving Photo EXIF GPS -> Real-time Device GPS -> Interactive Map Pin Drop.
- **Serverless & Container Adaptability**: Deployable as unified serverless functions on Vercel or as traditional standalone containers.

## Architectural Layers

### 1. Presentation Layer (`frontend/src`)
- **Purpose**: Render responsive user interfaces, capture civic issues, display geospatial heatmaps, and handle real-time status tracking.
- **Core Components**:
  - Context Providers: `AuthContext.tsx` (session and RBAC state), `LanguageContext.tsx` (dynamic translation and locale sync), `NotificationContext.tsx` (system toasts and inbox alerts).
  - Portal Routing: `App.tsx` guarded by `ProtectedRoute.tsx` and partitioned by role (`/citizen`, `/department-head`, `/staff`, `/admin`, `/developer/console`).
  - Dynamic Translators: Native i18n utilities (`translateStatus`, `translatePriority`, `translateCategory`, `translateDepartment`) dynamically rendering database values in English, Hindi, or Marathi without altering stored records.

### 2. API Gateway & Middleware Layer (`backend/src`)
- **Purpose**: Authenticate requests, enforce rate limits, validate JSON schemas, and route traffic to service controllers.
- **Components**:
  - `app.js`: Express application instance, CORS configuration, static upload serving with CSP headers, and centralized error handling.
  - `middleware/auth.js`: JWT signature verification, role entitlement checks (`requireRole`), and Supabase Auth session token validation.
  - `middleware/rateLimiter.js`: Tiered rate limiting (exponential backoff for auth, high-throughput for public telemetry).
  - `middleware/validateInput.js`: Joi schema enforcement blocking malformed coordinates, missing files, or unauthorized statuses.

### 3. Business Service Layer (`backend/src/services`)
- **Purpose**: Execute civic complaint lifecycle rules, calculate SLAs, perform duplicate detection, and automate staff task assignment.
- **Key Services**:
  - `locationService.js`: Parses EXIF metadata via `exifr`, validates Nashik bounds, calculates Haversine spatial distances, and checks for existing duplicates within a 100-meter radius.
  - `aiService.js`: Orchestrates calls to the Python AI service, manages failover to Gemini Vision API, and applies rule-based heuristic category matching.
  - `autoAssignmentService.js`: Evaluates field staff workload across departments, selects optimal assignees based on 0-task priority, performance metrics, and fair round-robin.
  - `departmentService.js`: Normalizes canonical department codes (`PWD`, `SAN`, `WTR`, `DRN`, `ELE`, `TRF`, `MNT`) and resolves department UUIDs.

### 4. AI & Computer Vision Layer (`ai_service`)
- **Purpose**: Deep-learning image analysis and municipal boundary validation.
- **Components**:
  - `main.py`: FastAPI application endpoints (`/analyze`, `/analyze-complaint-image`, `/google-maps/*`).
  - `model_manager.py`: In-memory model caching for the 4 civic defect models (`civicmodel`, `wasteModel`, `waterPipeModel`, `drainageModel`).
  - `analyzer.py`: LangGraph state graph evaluating detection boxes, confidence thresholds, and specific defect descriptions.
  - `google_maps_service.py`: Nashik municipal polygon containment and official route calculation.

### 5. Data & Persistence Layer (`backend/src/config/db.js` & `supabase`)
- **Purpose**: Abstract database communication and provide consistent SQL execution across different SQL dialects.
- **Components**:
  - `query()` function: Unified query interface translating parameter syntax (`?` vs `$1, $2`) and normalizing returned result structures (`rows`, `rowCount`).
  - `supabaseStorage.js`: Handles file streaming to Supabase Storage and returns permanent HTTPS URLs.

## Data Flow: Citizen Complaint Lifecycle

```
[Citizen Uploads Photo]
         │
         ▼
[Frontend: exifr parses EXIF GPS] ──(Fallback)──> [Device GPS / Interactive Map Pin]
         │
         ▼
[Backend: POST /api/complaints/analyze-upload]
         │
         ├──> [AI Microservice: YOLOv8 + LangGraph Classification]
         │        └── Returns: Category, Confidence, Severity, Specific Issue
         │
         ├──> [LocationService: 100m Duplicate Proximity Detection]
         │
         ▼
[Frontend: Citizen Reviews Pre-filled Complaint & Confirms]
         │
         ▼
[Backend: POST /api/complaints/submit]
         │
         ├──> [SLA Calculation: Water/Sanitation (24h), Drainage/Elec (48h), PWD (15d)]
         ├──> [Auto-Assignment Engine: Matches Department Staff with Lowest Active Load]
         ├──> [Supabase Storage: Media uploaded to permanent HTTPS bucket URL]
         ├──> [Database INSERT: complaints table updated with Status 'Submitted' / 'Staff Assigned']
         │
         ▼
[HOD / Staff Portals: Real-time Notification & Task Delivery]
         │
         ▼
[Staff Resolves: Uploads After-Photo & Materials Used]
         │
         ▼
[HOD Verifies & Approves: Complaint Marked 'Resolved']
```

## Key Abstractions

- **Canonical Department Mapping**: Fixed set of 7 municipal departments (`PWD`, `SAN`, `WTR`, `DRN`, `ELE`, `TRF`, `MNT`) with mapped UUIDs and category dictionaries.
- **Database Query Abstraction (`backend/src/config/db.js`)**: Encapsulates both `pg.Pool` and `sqlite3.Database` behind a single `query(sql, params)` contract.
- **Universal Image URL Resolver (`getValidImageUrl`)**: Transparently converts relative `/uploads/` paths, Supabase Storage object names, and raw base64 data URIs into absolute displayable URLs across all portals.

## Entry Points

- **Development Bootstrapper**: `start-dev.js` launches AI Service (:8000), Backend (:5000), and Frontend (:3000) concurrently with signal cleanup.
- **Frontend SPA**: `frontend/src/main.tsx` mounts React root into `frontend/index.html`.
- **Backend API Server**: `backend/src/server.js` initializes database connections, runs table migrations, and binds HTTP listeners.
- **Vercel Serverless Function**: `api/index.js` exports Express instance as a serverless handler for Vercel edge deployment.
- **AI Microservice**: `ai_service/main.py` starts Uvicorn ASGI server with pre-loaded models in memory.

---
*Architecture documentation verified against active application routes and services on 2026-10-23.*
