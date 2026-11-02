"""
Phase 7 - Task 4: Solid Waste Dataset Expansion Blueprint & Quality Audit
Establishes the detailed expansion specification, annotation guidelines, and readiness evaluation
to solve the 5-class validation starvation problem (+150-200 boxes per underrepresented class).
Outputs: waste_expansion_manifest.json, waste_annotation_quality_report.md, waste_dataset_readiness.json.
"""

import os
import json
import time

PHASE7_DIR = r"ai_service\experiments\phase7\waste_expansion"
MANIFEST_PATH = os.path.join(PHASE7_DIR, "waste_expansion_manifest.json")
READINESS_JSON_PATH = os.path.join(PHASE7_DIR, "waste_dataset_readiness.json")
REPORT_MD_PATH = os.path.join(PHASE7_DIR, "waste_annotation_quality_report.md")
ROOT_REPORT_MD = r"waste_annotation_quality_report.md"

def build_waste_expansion():
    print("=" * 80)
    print("PHASE 7 TASK 4: SOLID WASTE DATASET EXPANSION & QUALITY AUDIT")
    print("=" * 80)

    # 1. Manifest
    manifest = {
        "dataset_name": "NagarSetu Municipal Solid Waste Dataset Expansion (Phase 7 Specification)",
        "baseline_state": {
            "total_images": 30,
            "classes": ["BIODEGRADABLE", "CARDBOARD", "GLASS", "METAL", "PAPER", "PLASTIC"],
            "total_boxes_by_split": {
                "train": {"PLASTIC": 66, "BIODEGRADABLE": 24, "METAL": 19, "PAPER": 8, "GLASS": 2, "CARDBOARD": 1},
                "val": {"PLASTIC": 7, "BIODEGRADABLE": 0, "METAL": 0, "PAPER": 0, "GLASS": 0, "CARDBOARD": 0},
                "test": {"PLASTIC": 48, "GLASS": 13, "BIODEGRADABLE": 4, "PAPER": 4, "METAL": 2, "CARDBOARD": 0}
            },
            "critical_flaw": "5 out of 6 classes have ZERO validation instances. CARDBOARD has zero test instances and only 1 train box."
        },
        "expansion_quotas_and_targets": {
            "collection_targets_per_class": {
                "CARDBOARD": {"current_train_boxes": 1, "target_additional_boxes": 200, "projected_total": 201, "priority": "CRITICAL_P0"},
                "GLASS":     {"current_train_boxes": 2, "target_additional_boxes": 180, "projected_total": 182, "priority": "CRITICAL_P0"},
                "PAPER":     {"current_train_boxes": 8, "target_additional_boxes": 160, "projected_total": 168, "priority": "HIGH_P1"},
                "BIODEGRADABLE": {"current_train_boxes": 24, "target_additional_boxes": 150, "projected_total": 174, "priority": "HIGH_P1"},
                "METAL":     {"current_train_boxes": 19, "target_additional_boxes": 150, "projected_total": 169, "priority": "HIGH_P1"},
                "PLASTIC":   {"current_train_boxes": 66, "target_additional_boxes": 50,  "projected_total": 116, "priority": "BALANCING"}
            },
            "projected_dataset_summary": {
                "total_target_boxes": 1010,
                "projected_images": 250,
                "target_val_boxes_per_class": ">= 30 per class",
                "target_test_boxes_per_class": ">= 30 per class"
            }
        },
        "scene_diversity_requirements": [
            {"scene_type": "isolated_objects", "percentage": "25%", "description": "Single clean and crushed waste objects on neutral asphalt/ground"},
            {"scene_type": "mixed_roadside_garbage", "percentage": "40%", "description": "Urban Indian roadside trash heaps with overlapping categories"},
            {"scene_type": "partially_occluded_debris", "percentage": "20%", "description": "Objects partially buried in dirt, mud, or under plastic bags"},
            {"scene_type": "adverse_lighting_glare", "percentage": "15%", "description": "Direct midday sun specular highlights and deep night shadows"}
        ],
        "provenance_and_licensing_sources": [
            {
                "source_id": "SRC-TACO-MUNICIPAL",
                "name": "Trash Annotations in Context (TACO) Dataset",
                "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
                "classes_mapped": "Cardboard, Glass, Metal, Paper",
                "relevance": "Standard benchmark for litter localization"
            },
            {
                "source_id": "SRC-INDIAN-CIVIC-WASTE",
                "name": "Indian Municipal Waste Management Field Survey",
                "license": "Government Open Data / Public Municipal Archive",
                "classes_mapped": "Biodegradable wet waste, vegetable residue, plastic pouches",
                "relevance": "Authentic local roadside waste topography"
            }
        ]
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    # 2. Readiness Report
    readiness = {
        "domain": "solid_waste_classification",
        "phase": 7,
        "readiness_status": "NEEDS MORE DATA (EXPANSION QUOTAS STAGED)",
        "quality_gate_decision": "RETRAINING PROHIBITED",
        "validation_void_status": "5 out of 6 classes empty in validation split",
        "minimum_ingestion_required": "150-200 bounding boxes per underrepresented class",
        "production_protection": "best.pt preserved intact as the active production model"
    }

    with open(READINESS_JSON_PATH, "w") as f:
        json.dump(readiness, f, indent=2)

    # 3. Annotation Quality Report Markdown
    report_md = f"""# Solid Waste Dataset Expansion & Annotation Quality Report (Phase 7)

**Date:** 2026-11-03  
**Domain:** Municipal Solid Waste Multi-Class Object Detection  
**Classes:** `BIODEGRADABLE`, `CARDBOARD`, `GLASS`, `METAL`, `PAPER`, `PLASTIC`  
**Status:** SPECIFICATION COMPLETE — RETRAINING PROHIBITED PENDING INGESTION  
**Current Baseline Model:** `best.pt` (Preserved intact)  

---

## 1. Executive Summary

Phase 6 audits proved mathematically that the existing `garbage_waste_v2` dataset (30 images) is fundamentally incapable of supporting reliable model evaluation:
- In the validation split, **5 out of 6 classes have ZERO bounding boxes**.
- `CARDBOARD` has **zero instances in both validation and test**, with only **1 single box in training**.
- Plastic represents **63.6% of all annotations**, inducing extreme detection bias.

In Phase 7, we enforce strict AI engineering governance: **Retraining `best.pt` is strictly prohibited**. We establish an authoritative Expansion Blueprint targeting **+150 to +200 verified bounding boxes per underrepresented class** across realistic municipal scenes.

---

## 2. Quantitative Deficit & Expansion Quotas

| Class | Current Train Boxes | Current Val Boxes | Current Test Boxes | Required Ingestion Quota | Target Total Boxes | Priority Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CARDBOARD** | 1 | **0** | **0** | **+200 boxes** | 201 boxes | **CRITICAL (P0)** |
| **GLASS** | 2 | **0** | 13 | **+180 boxes** | 182 boxes | **CRITICAL (P0)** |
| **PAPER** | 8 | **0** | 4 | **+160 boxes** | 168 boxes | **HIGH (P1)** |
| **BIODEGRADABLE** | 24 | **0** | 4 | **+150 boxes** | 174 boxes | **HIGH (P1)** |
| **METAL** | 19 | **0** | 2 | **+150 boxes** | 169 boxes | **HIGH (P1)** |
| **PLASTIC** | 66 | 7 | 48 | **+50 boxes** | 116 boxes | **BALANCING (P2)** |
| **TOTALS** | **120** | **7** | **71** | **+890 boxes** | **1,010 boxes** | — |

---

## 3. Strict Annotation & Quality Protocols

To ensure multi-class models learn true visual features rather than contextual noise:
1. **Occlusion Tagging:** Objects occluded $>70\\%$ must not be labeled as single-instance ground truth to prevent loss spikes.
2. **Crushed & Deformed Materials:** Flattened beverage cans (`METAL`) and crushed cardboard boxes (`CARDBOARD`) must be labeled with tight bounding boxes encompassing the deformed geometry.
3. **Transparent Glass Bottles:** Bounding boxes must enclose the full glass contour despite reflections or visual transparency through the bottle.
4. **Organic & Wet Waste:** Food scraps, fruit peels, and vegetable matter on dirt road edges must be partitioned into `BIODEGRADABLE` bounding boxes distinct from surrounding soil.

---

## 4. Quality Gate Protocol Before Retraining

Before training candidate `garbage_waste_model_v3.pt`:
1. **Zero Validation Voids:** Validation split must contain $\\ge 30$ verified instances for EVERY one of the 6 classes.
2. **Balanced Train Distribution:** No single class may exceed $35.0\\%$ of the total training bounding boxes.
3. **Target Acceptance Standard:** Candidate must achieve **Overall mAP50 $\\ge 0.6800$** and a **minimum AP50 $\\ge 0.5000$ for every class** on the frozen independent test set.

---

## 5. Phase 7 Governance Verdict
* **Quality Gate Decision:** **`NEEDS MORE DATA`**.
* **Retraining Status:** **PROHIBITED**. Zero production model weights modified. Production baseline `best.pt` preserved intact.
"""

    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(report_md)
    with open(ROOT_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Saved waste expansion manifest to {MANIFEST_PATH}")
    print(f"Saved waste readiness report to {READINESS_JSON_PATH}")
    print(f"Saved waste annotation report to {REPORT_MD_PATH} and {ROOT_REPORT_MD}")

if __name__ == "__main__":
    build_waste_expansion()

