"""
Phase 12 Tasks 3, 4 & 5: Annotation Schema, Guidelines & Collection Tracker
Generates:
1. phase12_annotation_schema.json (Formal JSON schema for dataset annotations)
2. phase12_collection_tracker.csv (CSV tracking 500-photo plan across 15 subscenarios)
"""

import os
import csv
import json

PHASE12_DIR = r"ai_service\experiments\phase12"
ANN_DIR = os.path.join(PHASE12_DIR, "annotations")
DATA_DIR = os.path.join(PHASE12_DIR, "data")
os.makedirs(ANN_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Generate Formal Annotation Schema
def generate_annotation_schema():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "NagarSetuWaterPipeAnnotationSchema_v12",
        "description": "Standardized schema for municipal water pipeline visual inspection and classification.",
        "type": "object",
        "required": [
            "image_id",
            "parent_id",
            "sha256",
            "dhash",
            "primary_class",
            "scenario_tags",
            "pipe_material",
            "review_status",
            "first_reviewer",
            "review_date",
            "dataset_split"
        ],
        "properties": {
            "image_id": {
                "type": "string",
                "pattern": "^WTR-P12-[0-9]{3}$",
                "description": "Unique identifier for the physical photograph."
            },
            "parent_id": {
                "type": "string",
                "pattern": "^WTR-PARENT-[0-9]{3}$",
                "description": "Parent photograph session identity for group-based split containment."
            },
            "cluster_id": {
                "type": "string",
                "pattern": "^CLUSTER-[0-9]{3}$",
                "description": "Perceptual dHash cluster ID (Hamming distance <= 5)."
            },
            "sha256": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
                "description": "SHA-256 cryptographic hash of the original raw photograph."
            },
            "dhash": {
                "type": "integer",
                "description": "64-bit difference hash for perceptual similarity."
            },
            "primary_class": {
                "type": "string",
                "enum": ["normal_pipe", "pipe_leak", "rusted_pipe", "uncertain_needs_review"],
                "description": "Primary high-level triage category."
            },
            "scenario_tags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "clean_intact",
                        "joint_flange_leak",
                        "high_pressure_spray",
                        "hairline_crack",
                        "microscopic_weeping",
                        "dry_surface_rust",
                        "corroded_joint",
                        "cold_pipe_condensation",
                        "humidity_droplets",
                        "wet_surface_non_leak",
                        "specular_glare",
                        "deep_shadow",
                        "underground_pit",
                        "paved_road_background"
                    ]
                },
                "minItems": 1,
                "description": "Granular environmental and physical condition descriptors."
            },
            "pipe_material": {
                "type": "string",
                "enum": [
                    "PVC_CPVC",
                    "Galvanized_Iron",
                    "Cast_Iron_Ductile",
                    "Copper",
                    "Reinforced_Concrete",
                    "Unknown_Metal"
                ]
            },
            "pipe_diameter_range": {
                "type": "string",
                "enum": ["< 1 inch", "1 - 3 inches", "4 - 8 inches", "> 8 inches", "unknown"]
            },
            "review_status": {
                "type": "string",
                "enum": [
                    "VERIFIED_SINGLE_REVIEW",
                    "VERIFIED_DUAL_REVIEW",
                    "FLAGGED_FOR_EXPERT_REVIEW",
                    "REJECTED_BLURRY_OR_INVALID"
                ]
            },
            "first_reviewer": {
                "type": "string",
                "description": "Identifier of the primary annotator."
            },
            "second_reviewer": {
                "type": ["string", "null"],
                "description": "Identifier of the verifying senior engineer (mandatory for edge cases)."
            },
            "review_date": {
                "type": "string",
                "format": "date",
                "description": "ISO 8601 date of review."
            },
            "dataset_split": {
                "type": "string",
                "enum": ["train", "val", "frozen_test"]
            },
            "source_permission": {
                "type": "string",
                "enum": ["INTERNAL_RESEARCH_VERIFIED", "FIELD_MUNICIPAL_SURVEY", "PUBLIC_DOMAIN"]
            }
        }
    }
    
    schema_path = os.path.join(ANN_DIR, "phase12_annotation_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    with open("phase12_annotation_schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Saved: {schema_path}")

# 2. Generate CSV Collection Tracker
def generate_collection_tracker():
    """
    Detailed tracker breaking down the 500-photo acquisition target into 15 specific municipal scenarios.
    Records:
    - Target photographs
    - Current verified independent photographs (summing to 85)
    - Remaining gap (summing to 415)
    - Review status and collection strategy
    """
    categories = [
        # Normal Pipes (Target: 100, Current: 23, Gap: 77)
        {
            "category_group": "A. Normal Pipes",
            "scenario": "Dry Clean PVC / CPVC",
            "target_photographs": 40,
            "verified_independent_photographs": 15,
            "remaining_quantity": 25,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "HIGH",
            "collection_method": "Municipal ward plumbing inventory audit (Ward 1-5)",
            "priority": "HIGH"
        },
        {
            "category_group": "A. Normal Pipes",
            "scenario": "Dry Clean Galvanized Iron (GI)",
            "target_photographs": 30,
            "verified_independent_photographs": 6,
            "remaining_quantity": 24,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "HIGH",
            "collection_method": "Overground domestic water supply riser inspection",
            "priority": "HIGH"
        },
        {
            "category_group": "A. Normal Pipes",
            "scenario": "Dry Intact Cast Iron (Uncorroded)",
            "target_photographs": 20,
            "verified_independent_photographs": 2,
            "remaining_quantity": 18,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "MEDIUM",
            "collection_method": "Sub-surface main distribution feeder line inspection",
            "priority": "MEDIUM"
        },
        {
            "category_group": "A. Normal Pipes",
            "scenario": "Copper / Brass Plumbing Lines",
            "target_photographs": 10,
            "verified_independent_photographs": 0,
            "remaining_quantity": 10,
            "annotation_completion_pct": 0.0,
            "reviewer_verification": "Pending Collection",
            "quality_status": "DEFICIT",
            "collection_method": "Water meter manifold survey",
            "priority": "MEDIUM"
        },

        # Active Leakage (Target: 150, Current: 57, Gap: 93)
        {
            "category_group": "B. Active Leakage",
            "scenario": "High-Pressure Spray Leaks",
            "target_photographs": 35,
            "verified_independent_photographs": 1,
            "remaining_quantity": 34,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Verified",
            "quality_status": "DEFICIT",
            "collection_method": "Emergency pipe breach response team telemetry",
            "priority": "CRITICAL"
        },
        {
            "category_group": "B. Active Leakage",
            "scenario": "Burst Joint / Flange Gasket Leakage",
            "target_photographs": 50,
            "verified_independent_photographs": 48,
            "remaining_quantity": 2,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "SUFFICIENT",
            "collection_method": "Municipal valve chamber inspections",
            "priority": "LOW"
        },
        {
            "category_group": "B. Active Leakage",
            "scenario": "Underground Weeping & Pavement Eruption",
            "target_photographs": 35,
            "verified_independent_photographs": 8,
            "remaining_quantity": 27,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "MEDIUM",
            "collection_method": "Road excavation water utility repair sessions",
            "priority": "HIGH"
        },
        {
            "category_group": "B. Active Leakage",
            "scenario": "Hairline Cracks & Capillary Drips",
            "target_photographs": 30,
            "verified_independent_photographs": 0,
            "remaining_quantity": 30,
            "annotation_completion_pct": 0.0,
            "reviewer_verification": "Pending Collection",
            "quality_status": "DEFICIT",
            "collection_method": "Macro close-up inspection during pressure testing",
            "priority": "CRITICAL"
        },

        # Rust & Corrosion (Target: 100, Current: 3, Gap: 97)
        {
            "category_group": "C. Rust & Corrosion",
            "scenario": "Dry Rust Scale Without Leakage",
            "target_photographs": 45,
            "verified_independent_photographs": 2,
            "remaining_quantity": 43,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "SEVERE_DEFICIT",
            "collection_method": "Aging cast-iron municipal water bridge lines",
            "priority": "CRITICAL"
        },
        {
            "category_group": "C. Rust & Corrosion",
            "scenario": "Surface Oxidation & Pitting Corrosion",
            "target_photographs": 35,
            "verified_independent_photographs": 1,
            "remaining_quantity": 34,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified",
            "quality_status": "SEVERE_DEFICIT",
            "collection_method": "Exposed atmospheric utility pipe lines",
            "priority": "CRITICAL"
        },
        {
            "category_group": "C. Rust & Corrosion",
            "scenario": "Rusted Couplings & Flange Bolts",
            "target_photographs": 20,
            "verified_independent_photographs": 0,
            "remaining_quantity": 20,
            "annotation_completion_pct": 0.0,
            "reviewer_verification": "Pending Collection",
            "quality_status": "DEFICIT",
            "collection_method": "Pumping station manifold valve rooms",
            "priority": "HIGH"
        },

        # Environmental & Surface Conditions (Target: 150, Current: 2, Gap: 148)
        {
            "category_group": "D. Environmental Conditions",
            "scenario": "Cold-Pipe Thermal Condensation",
            "target_photographs": 50,
            "verified_independent_photographs": 2,
            "remaining_quantity": 48,
            "annotation_completion_pct": 100.0,
            "reviewer_verification": "Dual-Verified (Flagged)",
            "quality_status": "SEVERE_DEFICIT",
            "collection_method": "Early morning chilled water supply riser surveys",
            "priority": "CRITICAL"
        },
        {
            "category_group": "D. Environmental Conditions",
            "scenario": "Humidity Beading & Rain Droplets",
            "target_photographs": 40,
            "verified_independent_photographs": 0,
            "remaining_quantity": 40,
            "annotation_completion_pct": 0.0,
            "reviewer_verification": "Pending Collection",
            "quality_status": "DEFICIT",
            "collection_method": "Post-rainfall outdoor municipal pipe photography",
            "priority": "HIGH"
        },
        {
            "category_group": "D. Environmental Conditions",
            "scenario": "Wet Pavement Without Pipe Breach",
            "target_photographs": 35,
            "verified_independent_photographs": 0,
            "remaining_quantity": 35,
            "annotation_completion_pct": 0.0,
            "reviewer_verification": "Pending Collection",
            "quality_status": "DEFICIT",
            "collection_method": "Road cleaning runoff near water conduits",
            "priority": "HIGH"
        },
        {
            "category_group": "D. Environmental Conditions",
            "scenario": "Harsh Sun Glare & Direct Reflections",
            "target_photographs": 25,
            "verified_independent_photographs": 0,
            "remaining_quantity": 25,
            "annotation_completion_pct": 0.0,
            "reviewer_verification": "Pending Collection",
            "quality_status": "DEFICIT",
            "collection_method": "Midday high-lux tropical sunlight photography",
            "priority": "MEDIUM"
        }
    ]

    csv_path = os.path.join(DATA_DIR, "phase12_collection_tracker.csv")
    fieldnames = [
        "category_group",
        "scenario",
        "target_photographs",
        "verified_independent_photographs",
        "remaining_quantity",
        "annotation_completion_pct",
        "reviewer_verification",
        "quality_status",
        "collection_method",
        "priority"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cat in categories:
            writer.writerow(cat)

    with open("phase12_collection_tracker.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cat in categories:
            writer.writerow(cat)

    print(f"Saved: {csv_path}")
    
    tot_target = sum(c["target_photographs"] for c in categories)
    tot_verified = sum(c["verified_independent_photographs"] for c in categories)
    tot_gap = sum(c["remaining_quantity"] for c in categories)
    print(f"Total Target: {tot_target} | Verified: {tot_verified} | Remaining Gap: {tot_gap}")
    assert tot_target == 500, f"Target sum mismatch: {tot_target}"
    assert tot_verified == 85, f"Verified sum mismatch: {tot_verified}"
    assert tot_gap == 415, f"Gap sum mismatch: {tot_gap}"

if __name__ == "__main__":
    generate_annotation_schema()
    generate_collection_tracker()

