# NagarSetu Solid Waste Annotation & Balancing Guidelines

## 1. Class Taxonomy & Material Differentiation

| Category | Primary Visual Signatures | Negative Rules (What NOT to label) |
| :--- | :--- | :--- |
| **`PLASTIC`** | Polythene bags, PET bottles, food wraps, plastic cups, synthetic packaging films. | Do not label painted metal cans or wax-coated paper as plastic. |
| **`BIODEGRADABLE`** | Food waste, vegetable peels, fruit discards, cut foliage, fallen dry leaves. | Do not label roadside soil, gravel, or pet waste as biodegradable. |
| **`CARDBOARD`** | Corrugated packing boxes, brown paperboard containers, folded shipping cartons. | Must have visible thickness/corrugation; single-sheet paper belongs in `PAPER`. |
| **`PAPER`** | Newspapers, receipts, flyers, cardboard drink cartons, loose stationery. | If heavily soaked with oil or organic slurry, label under `BIODEGRADABLE`. |
| **`METAL`** | Aluminum beverage cans, tin food cans, foil wraps, iron scraps, bottle caps. | Do not label metallic painted plastic as metal. |
| **`GLASS`** | Whole or broken glass bottles, jars, window shards, drinking glassware. | Do not label clear transparent plastic PET bottles as glass. |

---

## 2. Multi-Object Bounding Box Rules
1. **No Mixed Super-Boxes**: Never draw a single large bounding box around a heap of mixed rubbish. Every distinct visible object must be annotated separately.
2. **Minimum Size Threshold**: Objects smaller than 25×25 pixels in 1080p images should NOT be annotated unless class identity is unambiguous.
3. **Occlusion & Clutter**: If an object is > 75% hidden behind other litter, omit it.
4. **Boundary Tightness**: Bounding box borders must fit within 2–3 pixels of the object boundary, excluding shadows and asphalt background.

---

## 3. Class Balance Enforcement
Field surveyors and dataset curators must strictly maintain the balanced quota of 680 train, 155 val, and 155 test images across all six materials to ensure that validation splits never have zero representation.

