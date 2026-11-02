# Drainage Dataset Expansion & Annotation Quality Report (Phase 7)

**Date:** 2026-11-03  
**Domain:** Municipal Stormwater Drainage Condition Classification  
**Status:** SPECIFICATION COMPLETE — RETRAINING HALTED PENDING INGESTION  
**Current Baseline Model:** `drainage_model.pt` (Preserved intact)  

---

## 1. Executive Summary

Phase 6 forensic audits conclusively established that the entire NagarSetu drainage dataset contains **only 6 verified normal drains out of 106 unique images (5.66%)**. Training a 3-class classifier (`normal_drain`, `blocked_drain`, `damaged_drain`) under this extreme negative-class scarcity creates severe operational risk: **clean municipal gutters are routinely flagged as blocked or damaged**, generating false alarms and wasting municipal resources.

In Phase 7, rather than artificially forcing retraining on inadequate data, we have formulated a rigorous **Expansion Manifest & Quality Architecture** requiring **+100 verified normal drains** before training can be authorized.

---

## 2. Ingestion Target Specification (+100 Normal Drains)

| Sub-Category | Required Image Quota | Visual Definition & Acceptance Standard | Operational Purpose |
| :--- | :--- | :--- | :--- |
| **Clean Concrete Gutters** | 30 images | Smooth concrete roadside drainage channels, zero standing water, zero silt deposits | High-frequency urban baseline |
| **Dry Culverts & Underpasses**| 25 images | Pre-monsoon dry municipal box/pipe culverts with clear throat and headwalls | Suburban & highway drainage |
| **Intact Metal Grates/Covers**| 25 images | Cast-iron, ductile iron, or welded steel grates firmly seated with unbroken bars | Pedestrian sidewalk grates |
| **Masonry & Stone Channels** | 20 images | Sound stone-pitching channels, mortar joints intact, clear waterpath | Traditional municipal channels |
| **Total Normal Targets** | **100 images** | Must be verified by human reviewer tool logged with SHA-256 | Rebalances dataset to **41.4% normal** |

---

## 3. Defect Category Refinement (+50 Defect Samples)

To prevent defect sub-type confusion, additional defect categories are staged:
1. **Vegetation Choke (15 images):** Dense root and weed growth blocking water intake.
2. **Silt Accumulation (10 images):** Heavy compacted sediment occupying >50% cross-sectional area.
3. **Spalled Concrete (15 images):** Structural curb fracture and spalling without total collapse.
4. **Missing Slab/Lid (10 images):** Dangerous open apertures requiring urgent hazard barricading.

---

## 4. Quality Gate Protocol Before Model Retraining

Before any new model checkpoint (e.g. `drainage_model_v3.pt`) can be trained:
1. **Deduplication:** Automated SHA-256 screening must confirm zero overlap with the 106 existing images.
2. **Label Discrepancy Protocol:** Any image where pre-classification and manual review differ must be placed in a separate review queue; no disputed label may enter the training split.
3. **Stratified Split:** Train (70%), Val (15%), Test (15%) must each contain $\ge 30\%$ normal drain samples.
4. **Acceptance Threshold:** Candidate must demonstrate **Normal Drain Recall $\ge 92.0\%$** and **Normal Drain Precision $\ge 90.0\%$** on the held-out test split.

---

## 5. Phase 7 Governance Verdict
* **Dataset Quality Gate:** **`NEEDS MORE DATA`**.
* **Retraining Status:** **BLOCKED**. Zero model weights modified. Production baseline `drainage_model.pt` preserved.
