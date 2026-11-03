# WATER AI DATASET ACQUISITION & ANNOTATION SPECIFICATION (PHASE 11)

## 1. Executive Summary & Objective

In accordance with Phase 11 directives, this specification establishes the standard operating procedure (SOP) for acquiring and annotating **500 genuinely independent original photographs** of municipal and domestic water supply pipelines.

> [!IMPORTANT]
> **SCIENTIFIC INTEGRITY DIRECTIVE:**
> - **Collection Objective:** 500 genuinely independent original photographs.
> - **Current Available Inventory on Disk:** 85 unique physical parent photographs.
> - **Current Net Shortfall:** 415 photographs.
> - **Fabrication Policy:** Strictly **0 synthetic images, 0 AI-generated images, and 0 crop-duplicated counts** are permitted.

---

## 2. Target 500-Image Class & Scenario Distribution Plan

| Category ID | Target Visual Condition | Minimum Target Count | Visual Feature Signature | Core Disambiguation Goal |
| :--- | :--- | :---: | :--- | :--- |
| **CAT-01** | Normal Pipes | 100 | Clean, dry surface, intact paint/galvanization, no puddles | Establish baseline normal signature across materials |
| **CAT-02** | Active Pressurized Water Leaks | 100 | High-velocity spray, water plumes, jet streams | Detect high-severity emergency pipe failures |
| **CAT-03** | Rusted Pipes Without Leakage | 80 | Red/brown iron oxide scaling, surface pitting, dry flaky rust | **Eliminate false alarms on dry oxidized pipes** |
| **CAT-04** | Cold-Pipe Condensation | 60 | Fine mist, uniform micro-droplets, dew rings from temperature delta | **Eliminate false alarms from thermal condensation** |
| **CAT-05** | Ambient Humidity & Water Droplets | 50 | Rain droplets, splash beads without source breach | Differentiate external water splash from pipe breach |
| **CAT-06** | Wet Surfaces Without Structural Leakage | 40 | Damp pavement, muddy background, dry intact pipe | Prevent background wetness from triggering pipe alarm |
| **CAT-07** | Hairline Cracks & Weeping Seepage | 40 | Micro-fracture, slow capillary seepage, wet dark seam | Catch subtle early-stage structural fatigue |
| **CAT-08** | Joint & Flange Gasket Seepage | 30 | Droplets forming at bolts, flange gap moisture | Identify connector gasket degradation |
| **Total** | **Comprehensive Water Pipe Dataset** | **500** | **Balanced across 10 environmental conditions** | **Generalizable municipal classification** |

---

## 3. Pipe Material & Environmental Diversity Matrix

1. **Pipe Materials:**
   - Polyvinyl Chloride (PVC / CPVC / UPVC) — 30% (150 images)
   - Galvanized Iron (GI) — 30% (150 images)
   - Cast Iron & Ductile Iron (CI / DI) — 25% (125 images)
   - Copper & Brass domestic lines — 10% (50 images)
   - Reinforced Concrete Pipes (RCP) — 5% (25 images)
2. **Lighting Conditions:**
   - Direct midday tropical sunlight (harsh glare, high specular reflections) — 30%
   - Overcast / Diffuse daylight — 30%
   - Deep shadow / Underground utility pit (low lux, flashlight/LED illuminated) — 25%
   - Dawn / Dusk golden hour — 15%
3. **Camera Perspectives:**
   - Normal incident angle ($90^\circ$ perpendicular to pipe axis) — 40%
   - Oblique angle ($45^\circ$ grazing angle to evaluate surface texture) — 35%
   - Close-up macro (within 15 cm of suspected leak or rust patch) — 25%

---

## 4. Annotation & Provenance Schema

Every acquired photograph must be cataloged with the following immutable fields:
- `sha256`: Cryptographic hash of the raw original camera file.
- `dhash`: Perceptual difference hash (8x8 grayscale) for near-duplicate rejection.
- `parent_image_id`: Unique identifier assigned to the physical photography session.
- `collection_timestamp`: ISO 8601 acquisition timestamp.
- `physical_location`: GPS or ward identifier (e.g. Pune Municipal Ward 12).
- `pipe_material`: Ground-truth confirmed pipe material.
- `surface_condition`: Validated ground truth (Normal, Spray, Drip, Rust, Condensation).
- `3class_label`: One of `['normal_pipe', 'pipe_leak', 'rusted_pipe']`.
- `annotation_reviewer`: Independent senior engineer sign-off.
- `dual_review_status`: Confirmed by 2 independent human annotators.

---

## 5. Current Physical Dataset Status (Phase 11 Baseline)

- **Total Unique Parents Cataloged:** 85
  - `pipe_leak`: 57 parent photographs
  - `normal_pipe`: 25 parent photographs
  - `rusted_pipe`: 3 parent photographs
- **Group Split Allocation:**
  - **Train Split:** 50 parents
  - **Validation Split:** 18 parents
  - **Frozen Independent Test Split:** 17 parents
- **Zero Cross-Split Leakage Confirmed:** Zero parent ID overlap and zero perceptual near-duplicates exist between the frozen test split and the training/validation splits.
