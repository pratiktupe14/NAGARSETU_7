# PHASE 9: DRAINAGE AI PRE-PRODUCTION READINESS AUDIT
**Generated:** 2026-11-03  
**Domain:** Urban Stormwater & Drainage Infrastructure  
**Current Production Model:** `drainage_model.pt` (ResNet18 / MobileNetV3 Architecture)  
**Evaluated Candidate Checkpoint:** `drainage_model_v2.pt` (Phase 2 Experimental)  
**Readiness Verdict:** **BLOCKED / NOT READY FOR PRODUCTION PILOT**  
**Guideline Adherence:** Zero premature retraining; rigorous blocker documentation

---

## 1. Executive Summary & Readiness Status

The Drainage AI system is classified as **NOT READY** for production deployment or shadow pilot operation. While the baseline model correctly distinguishes clear structural openings from severe obstructions in high-visibility conditions, empirical auditing reveals severe sensitivity to seasonal environmental factors, water turbidity, and silt accumulation.

Premature retraining on existing limited datasets (109 raw images on local disk) would lead to catastrophic overfitting. A rigorous dataset expansion and annotation campaign must precede any production promotion.

---

## 2. Current Asset & Model Inventory

- **Production Baseline Model:** `ai_service/model/drainage_model.pt` (SHA-256 verified)
- **Experimental Checkpoint:** `ai_service/experiments/phase2/drainage/drainage_model_v2.pt`
- **Local Photographic Corpus:** 109 uncurated images in `D:\NAGARSETU\drainage images`
- **Classes Defined:** `clean_drain`, `blocked_drain`, `overflowing_drain`

### Baseline vs. Candidate Audit Findings
In Phase 2 testing, `drainage_model_v2.pt` exhibited higher nominal recall on simulated debris piles, but generated high false alarm rates on dry culverts containing dead leaves, dry sand, or shadow gradients. It failed to generalize across varying municipal culvert geometries (box culverts, open masonry drains, precast concrete pipes).

---

## 3. Critical Production Blockers

1. **Extreme Seasonal & Monsoon Data Void:**
   The training corpus lacks verified monsoon flash-flood imagery, high-velocity muddy runoff, submerged grates, and nocturnal back-flow conditions.
2. **Water Surface Reflections & Floating Debris Ambiguity:**
   Floating fallen leaves or shadows cast by roadside trees are misclassified as structural blockages ($FPR > 24\%$ on sunny days).
3. **Culvert Architecture Variance Across Urban Wards:**
   Precast RCC pipes, open stone channels, and brick-lined subterranean drains have radically different visual baselines that cannot be represented by a single monolithic classification boundary.
4. **Lack of Bounding Box / Segmentation Ground Truth:**
   Current annotations are whole-image classification tags. Municipal field crews require spatial localization to discern whether a blockage is at the inlet, outlet, or interior grate.

---

## 4. Mandatory Pre-Requisites for Future Phases

Before any retraining can be approved:
1. **Acquire 800+ Geotagged Field Images:**
   - 250 Dry masonry culverts (normal baseline)
   - 200 Silted drains with partial blockage (>50% cross-section)
   - 200 Monsoon overflowing drains with turbulent surface water
   - 150 Precast concrete storm sewer grates
2. **Transition from Image Classification to Object Detection:**
   Annotate debris, silt, plastic dams, and grate structures using YOLOv8 bounding boxes rather than global image tags.
3. **Cross-Ward Validation Split:**
   Split validation sets by geographic municipal ward to guarantee models generalize to unseen drainage infrastructure.
