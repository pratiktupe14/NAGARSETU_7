"""
Phase 6 - Task 1: Drainage Dataset Arithmetic Forensics
Investigating why Phase 5 class totals (50 damaged + 49 blocked + 6 normal = 105) differed from 102 unique physical images.
Auditing physical files, SHA-256 hashes, review metadata, and multi-label/duplicate interactions.
"""

import os
import json
import hashlib
from collections import Counter

DISK_DIR = r"D:\NAGARSETU\drainage images"
CATALOG_PATH = r"ai_service\data\drainage_catalog.json"
REVIEWED_PATH = r"ai_service\training\drainage_v2\drainage_annotations_reviewed.json"
P5_MANIFEST_PATH = r"ai_service\experiments\phase5\drainage_reconciliation\reconciled_drainage_manifest.json"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def forensic_audit():
    print("=" * 80)
    print("PHASE 6 TASK 1: DRAINAGE DATASET ARITHMETIC FORENSICS")
    print("=" * 80)

    # 1. Physical Files on Disk
    disk_files = {}
    hash_to_files = {}
    if os.path.exists(DISK_DIR):
        for fn in sorted(os.listdir(DISK_DIR)):
            fp = os.path.join(DISK_DIR, fn)
            if os.path.isfile(fp):
                h = sha256_file(fp)
                disk_files[fn] = {"path": fp, "sha256": h, "size": os.path.getsize(fp)}
                hash_to_files.setdefault(h, []).append(fn)

    print(f"1. Physical files in '{DISK_DIR}': {len(disk_files)}")
    print(f"   Unique SHA-256 hashes on disk: {len(hash_to_files)}")
    exact_duplicates = {h: flist for h, flist in hash_to_files.items() if len(flist) > 1}
    print(f"   Duplicate hash clusters on disk: {len(exact_duplicates)}")
    for h, flist in exact_duplicates.items():
        print(f"     Cluster {h[:12]}... ({len(flist)} files): {flist}")

    # 2. Review JSON
    with open(REVIEWED_PATH, "r", encoding="utf-8") as f:
        rev_data = json.load(f)
    rev_images = rev_data.get("images", [])
    rev_meta = rev_data.get("review_metadata", {})

    print(f"\n2. Reviewed JSON images count: {len(rev_images)}")
    print(f"   review_metadata: {rev_meta.get('class_counts')}")
    # Note in review_metadata: {'normal_drain': 6, 'blocked_drain': 49, 'damaged_drain': 51, 'overflow_drain': 9}
    # Notice: 6 + 49 + 51 = 106! And 106 images in rev_images!

    # 3. Check filenames in reviewed JSON vs disk
    rev_filenames = [img["filename"] for img in rev_images]
    rev_filenames_set = set(rev_filenames)
    disk_filenames_set = set(disk_files.keys())

    in_rev_not_disk = rev_filenames_set - disk_filenames_set
    in_disk_not_rev = disk_filenames_set - rev_filenames_set

    print(f"\n3. Filenames in reviewed JSON but NOT on disk ({len(in_rev_not_disk)}):")
    for f in in_rev_not_disk:
        # Find which entry this is
        entry = next(img for img in rev_images if img["filename"] == f)
        print(f"     {f} -> assigned: {entry.get('assigned_label')}, sha: {entry.get('sha256')[:12]}")

    print(f"\n   Filenames on disk but NOT in reviewed JSON ({len(in_disk_not_rev)}):")
    for f in in_disk_not_rev:
        print(f"     {f} -> sha: {disk_files[f]['sha256'][:12]}")

    # 4. Check assigned_label counts across ALL 106 reviewed images
    all_rev_counts = Counter(img.get("assigned_label") for img in rev_images)
    print(f"\n4. Assigned labels across ALL 106 reviewed JSON entries:")
    print(f"   {dict(all_rev_counts)}")

    # 5. Check duplicate entries in reviewed JSON
    # Check if duplicate files appear in rev_images
    rev_hashes = {}
    for img in rev_images:
        h = img.get("sha256")
        rev_hashes.setdefault(h, []).append(img["filename"])

    rev_dup_clusters = {h: flist for h, flist in rev_hashes.items() if len(flist) > 1}
    print(f"\n5. Duplicate SHA-256 clusters in reviewed JSON ({len(rev_dup_clusters)} clusters):")
    for h, flist in rev_dup_clusters.items():
        print(f"     {h[:12]}... -> {flist}")

    # 6. Trace what happened in Phase 5:
    # Phase 5 script did:
    # unique_records = [r for r in reconciliation_records if not r["is_exact_duplicate"]]
    # rev_unique_counts = Counter(r["reviewed_assigned_label"] for r in unique_records if r["reviewed_assigned_label"])
    # Let's inspect the exact reconciliation_records from Phase 5 manifest!
    with open(P5_MANIFEST_PATH, "r", encoding="utf-8") as f:
        p5_manifest = json.load(f)

    p5_records = p5_manifest.get("dataset_records", [])
    print(f"\n6. Phase 5 Manifest analysis:")
    print(f"   Total records in p5_manifest: {len(p5_records)}")
    dup_records = [r for r in p5_records if r.get("is_exact_duplicate")]
    non_dup_records = [r for r in p5_records if not r.get("is_exact_duplicate")]
    print(f"   Duplicate records flagged: {len(dup_records)}")
    for d in dup_records:
        print(f"     DUP: {d['filename']} (dup of {d['duplicate_of']}) - cat:{d['catalog_label']} rev:{d['reviewed_assigned_label']}")
    print(f"   Non-duplicate records: {len(non_dup_records)}")

    p5_non_dup_labels = Counter(r.get("reviewed_assigned_label") for r in non_dup_records if r.get("reviewed_assigned_label"))
    print(f"   Non-dup reviewed assigned label counts: {dict(p5_non_dup_labels)}")
    print(f"   Sum of counts: {sum(p5_non_dup_labels.values())}")

    # Check which records have reviewed_assigned_label == None
    no_rev = [r for r in non_dup_records if not r.get("reviewed_assigned_label")]
    print(f"   Non-dup records without reviewed label: {len(no_rev)}")
    for nr in no_rev:
        print(f"     {nr['filename']} (exists_on_disk={nr.get('exists_on_disk')})")

    # Now let's check unique physical images on disk and their labels
    # What are the unique physical images on disk?
    print(f"\n7. PHYSICAL DISK UNIQUE IMAGES AUDIT:")
    # For each unique sha on disk, find its canonical image and its reviewed label
    disk_unique_records = []
    for h, files in hash_to_files.items():
        canonical_fn = sorted(files)[0]
        # find in rev_images
        rev_entry = next((img for img in rev_images if img["filename"] in files or img["sha256"] == h), None)
        disk_unique_records.append({
            "sha256": h,
            "canonical_file": canonical_fn,
            "all_files": files,
            "is_duplicate_set": len(files) > 1,
            "assigned_label": rev_entry.get("assigned_label") if rev_entry else "UNLABELED",
            "is_overflow": rev_entry.get("is_overflow", False) if rev_entry else False
        })

    disk_unique_counts = Counter(r["assigned_label"] for r in disk_unique_records)
    print(f"   Unique physical images on disk: {len(disk_unique_records)}")
    print(f"   Class breakdown across unique physical images on disk: {dict(disk_unique_counts)}")

if __name__ == "__main__":
    forensic_audit()

