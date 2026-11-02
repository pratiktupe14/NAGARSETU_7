# NagarSetu Drainage Dataset Collection & Annotation Guidelines

## 1. Collection Scope & Field Protocol
To resolve the 5.6% negative-class starvation identified in Phase 1 and Phase 2, field teams and municipal surveyors must collect at least **100 additional verified normal-drain images** across varied urban, suburban, and monsoon conditions.

### Required Categories:
1. **Normal Concrete Gutters (Target: +60 Images)**:
   - Clean, functional roadside drains with unbroken concrete slabs or iron grates.
   - Water flowing freely without stagnation, algae bloom, or floating debris.
   - Must cover bright midday sunlight, overcast monsoon lighting, and dusk shadows.
2. **Clean Dry Culverts (Target: +40 Images)**:
   - Natural stormwater culverts during dry months.
   - May contain natural sand/pebbles, but must show intact walls and clear throat openings.
3. **Silt-Blocked Drains (Target: +25 Images)**:
   - Heavy silt accumulation filling > 50% of the drain cross-section.
   - Vegetation/weeds rooted inside drain channels choking velocity.
4. **Damaged Drains & Structural Collapse (Target: +25 Images)**:
   - Missing or fractured manhole lids and pedestrian grates.
   - Broken side walls exposing soil or undermining pavement.
5. **Drain Overflow (Target: +20 Images)**:
   - Water exceeding curb height flooding road shoulders.

---

## 2. Image Quality & Acquisition Constraints
- **Minimum Resolution**: 1280×720 pixels (prefer native 12MP smartphone capture).
- **Aspect Ratio**: Standard 4:3 or 16:9 landscape framing.
- **Angle Diversity**: 45° oblique perspective showing both road curb and drain depth, plus 90° top-down shots.
- **Exclusions**:
  - Do NOT capture motion-blurred images taken from moving vehicles.
  - Do NOT submit burst shots taken within < 2 meters of the same defect (prevents data leakage).
  - Do NOT crop out the surrounding curb/ground context.

---

## 3. Annotation Decision Matrix

| Visual Indicator | Assigned Category | Severity Level | Department SLA |
| :--- | :--- | :--- | :--- |
| Unbroken cover, flowing water, clean gutter | `normal_drain` | `None` | N/A |
| Light dust / dry season pebbles (< 10% volume) | `normal_drain` | `None` | N/A |
| Garbage pile blocking grate opening | `blocked_drain` | `Medium` | 48 Hours |
| Silt / sludge filling > 50% depth | `blocked_drain` | `Medium` | 48 Hours |
| Standing black stagnant water with foul scum | `blocked_drain` | `High` | 24 Hours |
| Fractured concrete slab (pedestrian hazard) | `damaged_drain` | `High` | 24 Hours |
| Missing drain cover / open cavity > 30cm | `damaged_drain` | `Critical` | 12 Hours |
| Water actively overtopping curb onto road | `blocked_drain` (flag `is_overflow=True`) | `Critical` | 12 Hours |

---

## 4. Ambiguity Resolution Protocol
- If a drain has both structural damage and garbage blockage, the higher hazard takes precedence: label as `damaged_drain` with sub-flag `has_blockage=True`.
- If an image cannot be categorized with > 90% human consensus, quarantine in `review_queue/` rather than forcing a label.

