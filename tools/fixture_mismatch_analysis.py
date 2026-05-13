from pathlib import Path
import csv
from src.parse_runsetup import load_runsetup
from src.parse_products import load_products
from src.match import load_mapping, match_all

root = Path(__file__).resolve().parents[1]
mapfile = load_mapping(root / 'mapping.yaml')
root_fixtures = root / 'tests' / 'fixtures'
extra_counts = {}
missing_counts = {}
for fixture in sorted(d for d in root_fixtures.iterdir() if d.is_dir() and d.name != '_catalogs'):
    rs = load_runsetup(fixture / 'runsetup.csv')
    catalog_name = (fixture / 'catalog.txt').read_text().strip()
    products = load_products(root_fixtures / '_catalogs' / catalog_name)
    _, _, _, pred = match_all(rs, products, mapfile)
    predicted_keys = {(p.thick, p.grade, p.color, p.width_token, p.length_token) for p in pred.values()}
    answer = set()
    with (fixture / 'answer_key.csv').open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            answer.add((row['thick'].strip(), row['grade'].strip(), row['color'].strip(), row['width_token'].strip(), row['length_token'].strip()))
    doc_thicks = {k[0] for k in answer}
    predicted_in_scope = {p for p in predicted_keys if p[0] in doc_thicks}
    extra = predicted_in_scope - answer
    missing = answer - predicted_in_scope
    for p in extra:
        extra_counts[p] = extra_counts.get(p, 0) + 1
    for p in missing:
        missing_counts[p] = missing_counts.get(p, 0) + 1
    print('FIX', fixture.name, 'extra', len(extra), 'missing', len(missing))

print('\nEXTRA freq top 20:')
for p, c in sorted(extra_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]:
    print(c, p)

print('\nMISSING freq top 20:')
for p, c in sorted(missing_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]:
    print(c, p)
