# Solid Waste Dataset Expansion & Annotation Quality Report (Phase 7)

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
1. **Occlusion Tagging:** Objects occluded $>70\%$ must not be labeled as single-instance ground truth to prevent loss spikes.
2. **Crushed & Deformed Materials:** Flattened beverage cans (`METAL`) and crushed cardboard boxes (`CARDBOARD`) must be labeled with tight bounding boxes encompassing the deformed geometry.
3. **Transparent Glass Bottles:** Bounding boxes must enclose the full glass contour despite reflections or visual transparency through the bottle.
4. **Organic & Wet Waste:** Food scraps, fruit peels, and vegetable matter on dirt road edges must be partitioned into `BIODEGRADABLE` bounding boxes distinct from surrounding soil.

---

## 4. Quality Gate Protocol Before Retraining

Before training candidate `garbage_waste_model_v3.pt`:
1. **Zero Validation Voids:** Validation split must contain $\ge 30$ verified instances for EVERY one of the 6 classes.
2. **Balanced Train Distribution:** No single class may exceed $35.0\%$ of the total training bounding boxes.
3. **Target Acceptance Standard:** Candidate must achieve **Overall mAP50 $\ge 0.6800$** and a **minimum AP50 $\ge 0.5000$ for every class** on the frozen independent test set.

---

## 5. Phase 7 Governance Verdict
* **Quality Gate Decision:** **`NEEDS MORE DATA`**.
* **Retraining Status:** **PROHIBITED**. Zero production model weights modified. Production baseline `best.pt` preserved intact.
