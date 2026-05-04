"""
match.py — Match Run Set Up Lumber rows to Comact AllProducts entries
using the rules in mapping.yaml.
"""
from __future__ import annotations

from pathlib import Path
import yaml


def load_mapping(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def match_for_row(row, products, run_species, mapping,
                  width_unmapped=None, length_unmapped=None,
                  apply_width_filter=False, apply_length_filter=False):
    """
    Return the subset of `products` satisfying this Lumber row.

    Hard constraints (always applied): species, thick, grade, color.
    Soft constraints (opt-in): width_band.min >= row.min_width_in,
                               length_band.min >= row.min_length_ft.

    The width/length tokens on Comact products describe which bin a board
    falls into, not whether the product is eligible for a destination.
    Activation is grade/color/thick/species driven; widths/lengths are
    plumbing inside the optimizer. Filters stay off by default until we
    confirm semantics against a labeled fixture.
    """
    allowed_grades = set(mapping["grade_map"].get(row.grade_code, []))
    allowed_colors = set(mapping["color_map"].get(row.color_code, []))
    width_tokens = mapping["width_tokens"]
    length_tokens = mapping["length_tokens"]

    matches = []
    for p in products:
        if p.species != run_species:
            continue
        if p.thick != row.thick:
            continue
        if p.grade not in allowed_grades:
            continue
        if p.color not in allowed_colors:
            continue

        # Track unmapped tokens regardless of filter mode (for diagnostics).
        if p.width_token not in width_tokens and width_unmapped is not None:
            width_unmapped.add(p.width_token)
        if p.length_token not in length_tokens and length_unmapped is not None:
            length_unmapped.add(p.length_token)

        if apply_width_filter:
            wband = width_tokens.get(p.width_token)
            if wband is None or wband["min"] < row.min_width_in:
                continue

        if apply_length_filter:
            lband = length_tokens.get(p.length_token)
            if lband is None or lband["min"] < row.min_length_ft:
                continue

        matches.append(p)
    return matches


def match_all(runsetup, products, mapping):
    width_unmapped = set()
    length_unmapped = set()
    out = []

    for row in runsetup.lumber_rows:
        ms = match_for_row(
            row,
            products,
            runsetup.species,
            mapping,
            width_unmapped=width_unmapped,
            length_unmapped=length_unmapped,
        )
        out.append((row, ms))

    return out, width_unmapped, length_unmapped


if __name__ == "__main__":
    from parse_runsetup import load_runsetup
    from parse_products import load_products

    runsetup_path = "tests/fixtures/softmaple_2026-04-27/runsetup.csv"
    products_path = "tests/fixtures/softmaple_2026-04-27/allproducts.xml"
    mapping_path = "mapping.yaml"

    rs = load_runsetup(runsetup_path)
    products = load_products(products_path)
    mapping = load_mapping(mapping_path)

    print(
        f"Run: {rs.species_raw} ({rs.species}), {rs.date}, {len(rs.lumber_rows)} Lumber rows"
    )
    print(
        "Catalog: "
        f"{len(products)} total products, "
        f"{sum(1 for p in products if p.species == rs.species)} in {rs.species}\n"
    )

    results, w_unmapped, l_unmapped = match_all(rs, products, mapping)
    unique = {}

    for row, matches in results:
        header = (
            f"{row.destination:8s} {row.thick:5s} {row.grade_code:3s} "
            f"{row.color_code:8s}  W>={row.min_width_in:>4} "
            f"L>={row.min_length_ft:>4}'  -> {len(matches)} matches"
        )
        print(header)
        for p in matches:
            print(f"    [{p.instance_id}] {p.name}")
            unique[p.instance_id] = p.name
        print()

    print("=" * 70)
    print(f"Unique active products predicted: {len(unique)}")
    print("Target (from 4/27/26 screenshot):  21")
    print("=" * 70)
    if w_unmapped:
        print(f"\nWidth tokens not in mapping.yaml: {sorted(w_unmapped)}")
    if l_unmapped:
        print(f"Length tokens not in mapping.yaml: {sorted(l_unmapped)}")

# ----- diagnostic: show every product available for this species -----
from collections import defaultdict
species_filter = "SMA"
print()
print("=" * 70)
print(f"Catalog dump: all {species_filter} products grouped by thick → grade")
print("=" * 70)
by_thick = defaultdict(list)
for p in products:
    if p.species == species_filter:
        by_thick[p.thick].append(p)
for thick in sorted(by_thick.keys()):
    plist = by_thick[thick]
    print(f"\n--- {thick} ({len(plist)} products) ---")
    for p in sorted(plist, key=lambda x: (x.grade, x.color, x.width_token)):
        print(f"  [{p.instance_id}] {p.grade:25} {p.color:6} "
              f"w={p.width_token:15} l={p.length_token:15}  {p.name}")