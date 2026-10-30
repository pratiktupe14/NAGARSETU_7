# Coding Conventions

**Analysis Date:** 2026-10-23
**Codebase:** NAGARSETU 3.1

## Naming Patterns

**Files & Directories:**
- React Components & Pages: `PascalCase.tsx` (e.g., `ReportIssuePage.tsx`, `LanguageSelector.tsx`).
- React Contexts: `PascalCase.tsx` ending with `Context` (e.g., `AuthContext.tsx`, `LanguageContext.tsx`).
- Frontend Services & Utilities: `camelCase.ts` (e.g., `complaintService.ts`, `i18n.ts`).
- Backend Route Handlers: `[domain].routes.js` (e.g., `complaint.routes.js`, `admin.routes.js`).
- Backend Services: `[domain]Service.js` (e.g., `autoAssignmentService.js`, `aiService.js`).
- Backend Tests: `[topic].test.js` or `[feature].js` in `backend/tests/` (e.g., `auto_staff_assignment.test.js`).
- Python Modules: `snake_case.py` (e.g., `model_manager.py`, `analyzer.py`).

**Functions & Variables:**
- Functions & Methods: `camelCase` (e.g., `resolveLocation`, `calculateSlaDeadline`, `getValidImageUrl`).
- React Custom Hooks: `use[Name]` (e.g., `useLanguage`, `useAuth`, `useNotifications`).
- Global Constants: `UPPER_SNAKE_CASE` (e.g., `ALLOWED_CATEGORIES`, `MAX_FILE_SIZE`, `CANONICAL_DEPARTMENTS`).
- Database Column Identifiers: `snake_case` in SQL and database models (e.g., `photo_before_url`, `assigned_staff_id`, `department_code`).

**TypeScript Types & Interfaces:**
- Types & Interfaces: `PascalCase` without `I` prefix (e.g., `UserProfile`, `Complaint`, `DepartmentRecord`, `SupportedLanguage`).
- Enums & Type Unions: `PascalCase` with string literal unions preferred (e.g., `type UserRole = 'citizen' | 'department_head' | 'service_staff' | 'city_admin' | 'super_admin'`).

## Code Style & Formatting

**Frontend (TypeScript / React):**
- Strict Type Checking: `noImplicitAny: true`, strict null checks enforced via `frontend/tsconfig.json`.
- React Component Signatures: Functional components using arrow functions or explicit `React.FC<Props>` declarations with typed props.
- CSS Styling: Pure Tailwind utility classes with responsive breakpoints (`sm:`, `md:`, `lg:`) and theme colors (`emerald-*`, `teal-*`, `slate-*`, `gray-*`).
- No Ad-hoc Inline Styles: All layout geometry, padding, and flexboxes utilize Tailwind classes.

**Backend (Node.js / Express):**
- CommonJS Module System: `const ... = require(...)` and `module.exports = ...`.
- Clean Controller Structure: Controllers extract params, delegate business logic to services, and return standardized JSON responses.
- Asynchronous Code: Standard `async`/`await` pattern with clean `try/catch` wrapping; avoid raw unhandled `.then()` chains.

## Import Organization

**Frontend Component Order:**
1. React core and hooks (`import React, { useState, useEffect } from 'react'`).
2. Third-party UI / icon libraries (`import { AlertTriangle, MapPin } from 'lucide-react'`).
3. Routing & routing utilities (`import { useNavigate, useParams } from 'react-router-dom'`).
4. Context hooks (`import { useLanguage } from '../../context/LanguageContext'`).
5. Application services & API clients (`import { submitComplaint } from '../../services/complaintService'`).
6. Custom components & layout wrappers (`import { DashboardLayout } from '../../components/DashboardLayout'`).
7. Types & domain contracts (`import { Complaint, UserProfile } from '../../types/database.types'`).

**Backend Module Order:**
1. Built-in Node.js modules (`path`, `fs`, `crypto`, `http`).
2. Third-party middleware & libraries (`express`, `cors`, `joi`, `jsonwebtoken`).
3. Configuration modules (`const { query } = require('../config/db')`).
4. Middleware functions (`authenticateToken`, `validateInput`).
5. Domain services (`locationService`, `aiService`).

## Error Handling & Security

**Error Handling Rules:**
- Centralized Error Middleware: `backend/src/middleware/errorHandler.js` catches all unhandled Express errors.
- Zero Information Leakage: In production (`NODE_ENV === 'production'`), error middleware returns generic, safe messages (e.g., `"Internal Server Error"`) and suppresses stack traces and internal query strings.
- Non-crashing Resilience: Database reconnection warnings and missing optional service warnings use `console.warn('[DATABASE NOTE] ...')` instead of crashing the process.

**Security Patterns:**
- **Rate Limiting**: Applied to all public, auth, and upload endpoints via `express-rate-limit`.
- **Magic-Byte Image Validation**: Multer stores images in memory; buffer headers are scanned for binary signatures (`\xff\xd8\xff` for JPEG, `\x89PNG` for PNG, `RIFF...WEBP` for WebP) before acceptance.
- **Credential Storage**: Passwords hashed using bcrypt; JWT secret length strictly enforced (>= 32 chars) in production.
- **SQL Injection Prevention**: All SQL queries execute via parameterized queries (`query('SELECT ... WHERE id = ?', [id])` or `$1, $2`).

## Localization (i18n) Guidelines

- **No Hardcoded English Strings**: All labels, tooltips, dialogs, form validation messages, and table headers must be invoked via `t('keyName')` from `useLanguage()`.
- **Tri-lingual Parity**: Every new key added to `frontend/src/utils/i18n.ts` must have valid, civic-appropriate entries in English (`en`), Hindi (`hi`), and Marathi (`mr`).
- **Dynamic Content Translators**: Dynamic database fields must pass through translator utilities:
  - Categories: `translateCategory(cat, language)`
  - Statuses: `translateStatus(status, language)`
  - Priorities: `translatePriority(priority, language)`
  - Departments: `translateDepartment(dept, language)`
- **Zero UI Layout Overflow**: Marathi and Hindi strings are often 20–30% longer than English equivalents. Containers must avoid fixed pixel widths on buttons and use responsive truncation or text wrapping.

---
*Conventions established and verified from existing production code patterns on 2026-10-23.*
