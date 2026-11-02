"""
Phase 7 - Task 3: Drainage Dataset Expansion Blueprint & Quality Audit
Establishes the detailed expansion specification, attribution manifest, and readiness evaluation
to solve the normal-class starvation problem (+100 verified normal drains target).
Outputs: drainage_expansion_manifest.json, drainage_annotation_quality_report.md, drainage_dataset_readiness.json.
"""

import os
import json
import time

PHASE7_DIR = r"ai_service\experiments\phase7\drainage_expansion"
MANIFEST_PATH = os.path.join(PHASE7_DIR, "drainage_expansion_manifest.json")
READINESS_JSON_PATH = os.path.join(PHASE7_DIR, "drainage_dataset_readiness.json")
REPORT_MD_PATH = os.path.join(PHASE7_DIR, "drainage_annotation_quality_report.md")
ROOT_REPORT_MD = r"drainage_annotation_quality_report.md"

def build_drainage_expansion():
    print("=" * 80)
    print("PHASE 7 TASK 3: DRAINAGE DATASET EXPANSION & QUALITY AUDIT")
    print("=" * 80)

    # 1. Drainage Expansion Manifest
    manifest = {
        "dataset_name": "NagarSetu Municipal Drainage Dataset Expansion (Phase 7 Specification)",
        "baseline_state": {
            "total_physical_files": 110,
            "duplicate_pairs": 4,
            "unique_images": 106,
            "classes": {
                "damaged_drain": 51,
                "blocked_drain": 49,
                "normal_drain": 6
            },
            "normal_drain_percentage": "5.66%"
        },
        "expansion_targets": {
            "target_additional_normal_drains": 100,
            "target_additional_blocked_drains": 25,
            "target_additional_damaged_drains": 25,
            "projected_total_dataset_size": 256,
            "projected_normal_drain_percentage": "41.4%"
        },
        "target_subcategories": {
            "normal_drain_controls": [
                {"category": "clean_paved_concrete_gutters", "quota": 30, "description": "Clean roadside concrete stormwater gutters with unobstructed flow"},
                {"category": "dry_culverts_and_underpasses", "quota": 25, "description": "Pre-monsoon dry municipal culverts free of silt and vegetation"},
                {"category": "intact_metal_grates_and_covers", "quota": 25, "description": "Structural cast-iron and steel grating without broken bars or missing sections"},
                {"category": "masonry_stone_lined_channels", "quota": 20, "description": "Traditional stone-masonry stormwater drains in sound functional order"}
            ],
            "defect_expansions": [
                {"category": "vegetation_and_weed_choke", "quota": 15, "description": "Overgrowth of weeds and grass obstructing drain throat"},
                {"category": "silt_and_sediment_buildup", "quota": 10, "description": "Fine soil and mud deposits exceeding 50% capacity"},
                {"category": "spalled_concrete_curb_damage", "quota": 15, "description": "Fractured concrete rim and curb inlet collapse"},
                {"category": "missing_or_displaced_lids", "quota": 10, "description": "Open pedestrian hazard from removed drainage slabs"}
            ]
        },
        "provenance_and_licensing_sources": [
            {
                "source_id": "SRC-MUNI-SURVEY-01",
                "organization": "Municipal Urban Development Infrastructure Surveys",
                "license": "Government Open Data / Public Municipal Inspection Archive",
                "attribution": "Public Domain Municipal Infrastructure Imagery (India Urban Datasets)",
                "collection_method": "Scheduled dry-season municipal infrastructure asset audit"
            },
            {
                "source_id": "SRC-CIVIC-COMMONS-02",
                "organization": "Wikimedia Commons / OpenStreetMap Ground Photos",
                "license": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)",
                "attribution": "Open Street Media Contributors (Indian Subcontinent Infrastructure)",
                "collection_method": "Geotagged verified infrastructure street photography"
            }
        ],
        "deduplication_and_leakage_safeguards": {
            "duplicate_hashing": "Mandatory SHA-256 pre-ingestion screening against 106 existing image hashes",
            "perceptual_hash_threshold": "pHash Hamming distance <= 4 flagged for human visual inspection",
            "split_isolation": "Burst photography from the same street segment allocated as an atomic block to train, val, or test"
        }
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    # 2. Dataset Readiness Evaluation
    readiness = {
        "domain": "drainage_condition_classification",
        "phase": 7,
        "readiness_status": "NEEDS MORE DATA (EXPANSION MANIFEST STAGED)",
        "quality_gate_decision": "BLOCKED FROM RETRAINING",
        "current_normal_count": 6,
        "required_normal_count": 106,
        "deficit": 100,
        "governing_rule": "Retraining drainage_model.pt or promoting drainage_model_v2.pt is strictly halted until the 100 verified normal drains are ingested and verified against Task 1 acceptance criteria."
    }

    with open(READINESS_JSON_PATH, "w") as f:
        json.dump(readiness, f, indent=2)

    # 3. Annotation Quality Report Markdown
    report_md = f"""# Drainage Dataset Expansion & Annotation Quality Report (Phase 7)

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
3. **Stratified Split:** Train (70%), Val (15%), Test (15%) must each contain $\\ge 30\\%$ normal drain samples.
4. **Acceptance Threshold:** Candidate must demonstrate **Normal Drain Recall $\\ge 92.0\\%$** and **Normal Drain Precision $\\ge 90.0\\%$** on the held-out test split.

---

## 5. Phase 7 Governance Verdict
* **Dataset Quality Gate:** **`NEEDS MORE DATA`**.
* **Retraining Status:** **BLOCKED**. Zero model weights modified. Production baseline `drainage_model.pt` preserved.
"""

    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(report_md)
    with open(ROOT_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Saved drainage expansion manifest to {MANIFEST_PATH}")
    print(f"Saved drainage readiness report to {READINESS_JSON_PATH}")
    print(f"Saved drainage annotation report to {REPORT_MD_PATH} and {ROOT_REPORT_MD}")

if __name__ == "__main__":
    build_drainage_expansion()

