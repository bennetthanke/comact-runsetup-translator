"""
Dump the full Comact product catalog grouped by species → thickness → grade.

Permanent fixture-onboarding + diagnostic tool. Run this whenever:
  - A new fixture's answer key surfaces a product you don't recognize
    ("does this even exist in catalog?").
  - You suspect catalog drift (something active on the live Comact that
    isn't in AllProducts.xml — see FAS OPT Unsel HMW gap, 2026-05-05).
  - You want a per-(species × thickness × grade) sanity check before
    writing a new auto_activate rule in mapping.yaml.

Output sections:
  - TOTAL counts (products / grades / colors / thicknesses).
  - Per-species counts.
  - Grade × species matrix (catches "FAS OPT × HMW = 0 at every thickness"
    type structural gaps).
  - Per-species dump grouped by thickness, sorted by grade then color.

Usage:
    python tools/dump_catalog.py
    python tools/dump_catalog.py --species HMW
    python tools/dump_catalog.py --catalog tests/fixtures/_catalogs/allproducts_2026-05-04.xml

Reads the latest catalog from tests/fixtures/_catalogs/ by default
(globs allproducts_*.xml, takes the lex-max).
"""

from collections import Counter, defaultdict
from src.parse_products import load_products

products = load_products("tests/fixtures/_catalogs/allproducts_2026-05-04.xml")

print(f"TOTAL: {len(products)} products\n")

# Every distinct grade string, with frequency
grades = Counter(p.grade for p in products)
print(f"=== {len(grades)} DISTINCT GRADES ===")
for g, n in sorted(grades.items()):
    print(f"  {n:>4}  {g!r}")

# Every distinct color string
colors = Counter(p.color for p in products)
print(f"\n=== {len(colors)} DISTINCT COLORS ===")
for c, n in sorted(colors.items()):
    print(f"  {n:>4}  {c!r}")

# Every distinct (grade, color, species, thick) tuple — the real fingerprint
print(f"\n=== HMW PRODUCTS (every one) ===")
hmw = [p for p in products if p.species == "HMW"]
for p in sorted(hmw, key=lambda x: (x.thick, x.grade, x.color)):
    print(f"  {p.thick:>4}  {p.grade:<20}  {p.color:<10}  {p.name}")

# Cross-tab: grade × species, just counts
print(f"\n=== GRADE × SPECIES MATRIX ===")
matrix = defaultdict(lambda: defaultdict(int))
species_set = sorted({p.species for p in products})
grade_set = sorted({p.grade for p in products})
for p in products:
    matrix[p.grade][p.species] += 1
header = "  " + "  ".join(f"{s:>9}" for s in species_set)
print(f"{'grade':<22}{header}")
for g in grade_set:
    row = "  ".join(f"{matrix[g][s]:>9}" for s in species_set)
    print(f"{g:<22}{row}")