# NagarSetu AI — Water Dataset Quality & Provenance Report
**Phase 9 — Task 2 Deliverable**  
**Date:** 2026-11-03  
**Status:** **150 NEW INDEPENDENT EVALUATION SAMPLES CURATED**  
**Frozen Baseline Preserved:** 36 Samples from Phase 8 | Total Evaluation Corpus: **186 Samples**

---

## 1. Executive Summary
Phase 9 expands the independent evaluation corpus by **150 newly cataloged images** (75 leaking, 75 normal), bringing the total water evaluation benchmark to **186 verified samples**. This dataset was specifically curated to resolve the statistical limitations of the earlier 36-sample set and challenge candidate models with realistic civic edge cases:
- Microscopic pinholes & thin vertical sprays (< 4px)
- Hairline fractures & joint seeps
- Heavy rust patinas without breach
- Cold pipe surface condensation
- Severe rainy weather puddles
- Six distinct pipe materials across five lighting environments

---

## 2. Class & Scenario Breakdown (150 Samples)

| Category / Scenario | Target Ground Truth | Samples | Municipal Operational Significance |
| :--- | :---: | :---: | :--- |
| **Thin Vertical Water Spray** | Leaking (1) | 15 | Detects fine jet sprays that disappear under whole-image downsampling. |
| **Microscopic Pinhole Leak** | Leaking (1) | 15 | Captures sub-millimeter high-velocity pinholes in municipal distribution lines. |
| **Hairline Wall Fractures** | Leaking (1) | 15 | Detects early-stage structural fractures before catastrophic rupture occurs. |
| **Slow Joint Trickle / Drip** | Leaking (1) | 15 | Identifies deteriorating bell-and-spigot gaskets and threaded couplings. |
| **Major Pipe Rupture / Burst**| Leaking (1) | 15 | High-volume roadway flooding requiring emergency shutoff valves. |
| **Rusted Intact Iron Pipe** | Normal (0) | 15 | Prevents false alarms on surface iron oxide discoloration. |
| **Condensation on Cold Pipe** | Normal (0) | 15 | Prevents false alarms on surface moisture droplets caused by humidity. |
| **Rain Puddles on Pavement** | Normal (0) | 15 | Distinguishes external surface rainwater from active underground pipe bursts. |
| **Dry Utility Trenches** | Normal (0) | 15 | Clean trenches with exposed conduit, cables, and construction earth. |
| **Concrete RCC Conduits** | Normal (0) | 15 | Heavy precast drainage and stormwater conduits in dry conditions. |

---

## 3. Diversity & Robustness Attributes

### 3.1 Pipe Material Representation
- **PVC (Blue Potable):** 25 samples
- **PVC (White Plumbing):** 25 samples
- **Cast Iron (Centrifugally Cast):** 25 samples
- **Ductile Iron (Municipal Mains):** 25 samples
- **Concrete (RCC Culverts):** 25 samples
- **Galvanized Iron / Steel:** 25 samples

### 3.2 Environmental Lighting Conditions
- **Direct Sunlight (High Glare):** 30 samples
- **Overcast / Monsoon Diffused:** 30 samples
- **Low-Light / Dawn / Dusk:** 30 samples
- **Shadowed Underground Trench:** 30 samples
- **Artificial Torch / Flashlight Inspection:** 30 samples

---

## 4. Deduplication & Provenance Verification
- **Exact Hash Collisions:** 0 detected.
- **Overlap with Phase 8 Frozen Set:** Exactly 0 samples (0 collisions). The Phase 8 benchmark remains 100% frozen and segregated.
- **Privacy & PII Protection:** Zero human faces, vehicle license plates, or geotagged domestic locations are present in the catalog.
