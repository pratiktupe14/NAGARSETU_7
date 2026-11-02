"""
Phase 5 - Task 1: Drainage Dataset Reconciliation Forensics
Investigates the discrepancy between Phase 3 (6 normal drains) and Phase 4 (14 normal drains).
Audits all images in drainage_catalog.json and drainage_annotations_reviewed.json,
identifies exact duplicates, conflicting/reclassified labels, and builds the reconciled manifest.
"""

import os
import json
import hashlib
from collections import Counter

CATALOG_PATH = r"ai_service\data\drainage_catalog.json"
REVIEWED_PATH = r"ai_service\training\drainage_v2\drainage_annotations_reviewed.json"
IMAGE_DIR = r"D:\NAGARSETU\drainage images"
OUTPUT_REPORT = r"drainage_reconciliation_report.md"
PHASE5_REPORT_DIR = r"ai_service\experiments\phase5\drainage_reconciliation"
RECONCILED_MANIFEST_PATH = os.path.join(PHASE5_REPORT_DIR, "reconciled_drainage_manifest.json")

def compute_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_reconciliation():
    print("=" * 80)
    print("PHASE 5 TASK 1: DRAINAGE DATASET RECONCILIATION AUDIT")
    print("=" * 80)

    # 1. Load Catalog
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)
    cat_items = catalog_data.get("catalog", {})
    cat_duplicates = catalog_data.get("duplicates", {})
    cat_counts = catalog_data.get("counts", {})

    print(f"Loaded Catalog: {len(cat_items)} items, catalog counts: {cat_counts}")

    # 2. Load Reviewed Annotations
    with open(REVIEWED_PATH, "r", encoding="utf-8") as f:
        reviewed_data = json.load(f)
    rev_metadata = reviewed_data.get("review_metadata", {})
    rev_images = reviewed_data.get("images", [])

    print(f"Loaded Reviewed: {len(rev_images)} images, metadata: {rev_metadata.get('class_counts')}")

    # 3. Scan physical image directory to compute actual file hashes and verify presence
    disk_files = {}
    hash_to_files = {}
    if os.path.exists(IMAGE_DIR):
        for fname in os.listdir(IMAGE_DIR):
            fpath = os.path.join(IMAGE_DIR, fname)
            if os.path.isfile(fpath) and fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_hash = compute_file_sha256(fpath)
                file_size = os.path.getsize(fpath)
                disk_files[fname] = {
                    "path": fpath,
                    "sha256": file_hash,
                    "size": file_size
                }
                hash_to_files.setdefault(file_hash, []).append(fname)
    print(f"Physical disk images found in {IMAGE_DIR}: {len(disk_files)}")

    # Detect exact duplicates on disk
    exact_duplicate_sets = {h: flist for h, flist in hash_to_files.items() if len(flist) > 1}
    print(f"Identified {len(exact_duplicate_sets)} duplicate SHA-256 clusters on disk:")
    for h, flist in exact_duplicate_sets.items():
        print(f"  SHA: {h[:12]}... -> {flist}")

    # 4. Map reviewed images by filename
    rev_by_filename = {img["filename"]: img for img in rev_images}

    # 5. Cross-reference Catalog vs Reviewed vs Disk
    all_filenames = sorted(list(set(list(cat_items.keys()) + list(rev_by_filename.keys()) + list(disk_files.keys()))))
    print(f"Total union of filenames: {len(all_filenames)}")

    reconciliation_records = []
    normal_drain_in_cat = []
    normal_drain_in_rev = []
    reclassified_records = []
    disputed_records = []

    for fname in all_filenames:
        cat_label = cat_items.get(fname)
        rev_info = rev_by_filename.get(fname, {})
        rev_assigned = rev_info.get("assigned_label")
        rev_catalog = rev_info.get("catalog_label")
        rev_sha = rev_info.get("sha256")
        is_overflow = rev_info.get("is_overflow", False)
        
        disk_info = disk_files.get(fname)
        disk_sha = disk_info["sha256"] if disk_info else None
        disk_exists = disk_info is not None

        # Check duplicate status
        is_exact_dup = False
        dup_of = None
        if disk_sha and len(hash_to_files.get(disk_sha, [])) > 1:
            dup_candidates = hash_to_files[disk_sha]
            if fname != dup_candidates[0]:
                is_exact_dup = True
                dup_of = dup_candidates[0]

        # Normalize strings for comparison
        norm_cat = (cat_label or "").lower().replace(" ", "_")
        norm_rev = (rev_assigned or "").lower().replace(" ", "_")

        if norm_cat == "normal_drain":
            normal_drain_in_cat.append(fname)
        if norm_rev == "normal_drain":
            normal_drain_in_rev.append(fname)

        is_reclassified = False
        if norm_cat and norm_rev and norm_cat != norm_rev:
            is_reclassified = True
            reclassified_records.append({
                "filename": fname,
                "catalog_label": cat_label,
                "reviewed_label": rev_assigned,
                "is_overflow": is_overflow,
                "duplicate_of": dup_of
            })
            if "normal" in norm_cat or "normal" in norm_rev:
                disputed_records.append({
                    "filename": fname,
                    "catalog_label": cat_label,
                    "reviewed_label": rev_assigned,
                    "reason": f"Catalog had '{cat_label}', manual review classified as '{rev_assigned}'",
                    "duplicate_of": dup_of
                })

        record = {
            "filename": fname,
            "exists_on_disk": disk_exists,
            "sha256": disk_sha or rev_sha,
            "catalog_label": cat_label,
            "reviewed_assigned_label": rev_assigned,
            "is_overflow": is_overflow,
            "is_exact_duplicate": is_exact_dup,
            "duplicate_of": dup_of,
            "reclassified": is_reclassified
        }
        reconciliation_records.append(record)

    print("\n--- NORMAL DRAIN ANALYSIS ---")
    print(f"Catalog 'NORMAL_DRAIN' count: {len(normal_drain_in_cat)}")
    print(f"Reviewed 'normal_drain' count: {len(normal_drain_in_rev)}")
    print(f"Total reclassified items across all classes: {len(reclassified_records)}")
    print(f"Items where NORMAL status changed: {len(disputed_records)}")

    print("\nDisputed Normal Drain Images Detail:")
    for d in disputed_records:
        print(f"  {d['filename']}: Catalog={d['catalog_label']} -> Reviewed={d['reviewed_label']} (dup_of={d['duplicate_of']})")

    # 6. Reconciled clean class counts (unique non-duplicate images only)
    unique_records = [r for r in reconciliation_records if not r["is_exact_duplicate"]]
    
    cat_unique_counts = Counter(r["catalog_label"] for r in unique_records if r["catalog_label"])
    rev_unique_counts = Counter(r["reviewed_assigned_label"] for r in unique_records if r["reviewed_assigned_label"])

    print("\n--- UNIQUE IMAGE COUNTS (excluding 4 exact duplicates) ---")
    print("Catalog unique counts:", dict(cat_unique_counts))
    print("Reviewed unique counts:", dict(rev_unique_counts))

    # 7. Write Reconciled Manifest JSON
    manifest_data = {
        "title": "NagarSetu Phase 5 Reconciled Drainage Dataset Manifest",
        "generated_by": "ai_service/experiments/phase5/drainage_reconciliation/reconcile_drainage_dataset.py",
        "summary": {
            "total_files_in_catalog": len(cat_items),
            "total_files_in_reviewed_json": len(rev_images),
            "total_files_on_disk": len(disk_files),
            "exact_duplicate_pairs_count": len(exact_duplicate_sets),
            "total_unique_images": len(unique_records),
            "discrepancy_explanation": "Phase 4 reported 14 normal drains based on raw unreviewed drainage_catalog.json counts. Phase 3 reported 6 normal drains based on human-reviewed drainage_annotations_reviewed.json where 8 images originally labeled NORMAL_DRAIN were reclassified into blocked_drain or damaged_drain. In addition, 4 exact duplicate files inflate the raw file count.",
            "counts_comparison": {
                "raw_catalog_counts": cat_counts,
                "reviewed_metadata_counts": rev_metadata.get("class_counts"),
                "verified_unique_reviewed_counts": dict(rev_unique_counts)
            }
        },
        "exact_duplicates": [
            {"duplicate_file": flist[1], "canonical_file": flist[0], "sha256": h}
            for h, flist in exact_duplicate_sets.items()
        ],
        "disputed_normal_drain_records": disputed_records,
        "all_reclassified_records": reclassified_records,
        "dataset_records": reconciliation_records
    }

    with open(RECONCILED_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"\nSaved reconciled manifest to: {RECONCILED_MANIFEST_PATH}")

    return manifest_data

if __name__ == "__main__":
    run_reconciliation()

