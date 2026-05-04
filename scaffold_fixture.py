"""
scaffold_fixture.py — create the folder skeleton for a new test fixture.

Usage:
    python scaffold_fixture.py <species> <date>

Examples:
    python scaffold_fixture.py sma 4-27-26
    python scaffold_fixture.py hmw 2026-05-11
    python scaffold_fixture.py rok 5/11/26

Creates tests/fixtures/<species>_<YYYY-MM-DD>/ with subdirs and an empty
answer_key.csv. Refuses to overwrite an existing fixture.
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# The 10 species in the Comact catalog (verified 2026-05-04 from AllProducts.xml).
# Anything else is a typo. Lowercase keys; we normalize input to lowercase.
KNOWN_SPECIES = {
    "sma",       # Soft Maple
    "hmw",       # Hard Maple White
    "ash",
    "cherry",
    "rok",       # Red Oak
    "wok",       # White Oak
    "walnut",
    "tul",       # Tulip / Yellow Poplar
    "basswood",
    "birch",
}

# Accept any of: 4-27-26, 04-27-26, 2026-04-27, 4/27/26, 04/27/2026, etc.
# Always return ISO YYYY-MM-DD.
DATE_FORMATS = (
    "%Y-%m-%d",   # 2026-04-27 (canonical)
    "%m-%d-%Y",   # 04-27-2026
    "%m-%d-%y",   # 4-27-26
    "%m/%d/%Y",   # 04/27/2026
    "%m/%d/%y",   # 4/27/26
)

def parse_date(raw: str) -> str:
    """Parse a date string in any of the accepted formats and return ISO YYYY-MM-DD."""
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(
        f"Couldn't parse date {raw!r}. Try one of: "
        f"YYYY-MM-DD, MM-DD-YY, MM-DD-YYYY, MM/DD/YY, MM/DD/YYYY."
    )

def validate_species(raw: str) -> str:
    """Lowercase + check against the catalog whitelist."""
    species = raw.strip().lower()
    if species not in KNOWN_SPECIES:
        raise ValueError(
            f"Unknown species {raw!r}. "
            f"Expected one of: {', '.join(sorted(KNOWN_SPECIES))}."
        )
    return species

def scaffold(species: str, iso_date: str, repo_root: Path) -> Path:
    """Create the fixture skeleton. Returns the fixture dir path."""
    fixture_dir = repo_root / "tests" / "fixtures" / f"{species}_{iso_date}"

    if fixture_dir.exists():
        raise FileExistsError(
            f"Fixture already exists: {fixture_dir}\n"
            f"  Refusing to overwrite. Delete it manually if you really mean to re-scaffold."
        )

    # Create the dir tree.
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "screenshots").mkdir()
    (fixture_dir / "notes").mkdir()

    # .gitkeep so empty subdirs survive a commit.
    (fixture_dir / "screenshots" / ".gitkeep").touch()
    (fixture_dir / "notes" / ".gitkeep").touch()

    # Empty answer_key.csv with the canonical header.
    answer_key = fixture_dir / "answer_key.csv"
    with answer_key.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["thick", "grade", "color", "width_token", "length_token"])

    # README.md stub — reminds you what goes where, in case you forget.
    readme = fixture_dir / "README.md"
    readme.write_text(
        f"# Fixture: {species} {iso_date}\n"
        f"\n"
        f"## Drop here\n"
        f"- `runsetup.xlsx` — original email attachment\n"
        f"- `runsetup.csv` — Save As CSV from the .xlsx\n"
        f"- `allproducts.xml` — only if catalog refreshed since last fixture\n"
        f"- `screenshots/<thick>_active.jpg` — Active Products, per thickness\n"
        f"- `screenshots/<thick>_available.jpg` — Available Products, per thickness\n"
        f"- `notes/<thick>.m4a` — voice memo if a deselect was non-obvious\n"
        f"\n"
        f"Then transcribe screenshots into `answer_key.csv` and run:\n"
        f"```\n"
        f"python tests/check_match.py tests/fixtures/{species}_{iso_date}\n"
        f"```\n",
        encoding="utf-8",
    )

    return fixture_dir

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a new test fixture folder for a Comact Run Set Up.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scaffold_fixture.py sma 4-27-26\n"
            "  python scaffold_fixture.py hmw 2026-05-11\n"
            "  python scaffold_fixture.py rok 5/11/26\n"
            f"\nKnown species: {', '.join(sorted(KNOWN_SPECIES))}"
        ),
    )
    parser.add_argument("species", help="Species code (e.g. sma, hmw, rok).")
    parser.add_argument(
        "date",
        help="Run date. Accepts YYYY-MM-DD, MM-DD-YY, MM-DD-YYYY, MM/DD/YY, MM/DD/YYYY.",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        species = validate_species(args.species)
        iso_date = parse_date(args.date)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parent

    try:
        fixture_dir = scaffold(species, iso_date, repo_root)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    rel = fixture_dir.relative_to(repo_root)
    print(f"✓ Created {rel}/")
    print(f"  Next: drop runsetup.xlsx + runsetup.csv into the folder,")
    print(f"        screenshot at the Comact, transcribe into answer_key.csv.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
