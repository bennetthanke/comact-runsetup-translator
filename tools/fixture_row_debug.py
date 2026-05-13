from pathlib import Path
import csv
import sys
from src.parse_runsetup import load_runsetup
from src.parse_products import load_products
from src.match import load_mapping, match_all, match_for_row

root = Path(__file__).resolve().parents[1]
fixture_name = sys.argv[1] if len(sys.argv) > 1 else 'ash_2026-05-06'
fixture = root / 'tests' / 'fixtures' / fixture_name
rs = load_runsetup(fixture / 'runsetup.csv')
mapping = load_mapping(root / 'mapping.yaml')
products = load_products(root / 'tests' / 'fixtures' / '_catalogs' / (fixture / 'catalog.txt').read_text().strip())
print('fixture:', fixture_name)
print('rows:', len(rs.lumber_rows))
for r in rs.lumber_rows:
    ms = match_for_row(r, products, rs.species, mapping)
    print('ROW', r.destination, r.thick, r.grade_code, r.color_code, r.min_width_in, r.min_length_ft, 'matches', len(ms))
    for p in ms:
        print('   ', p.grade, p.color, p.thick, p.width_token, p.length_token)

print('\nPREDICTIONS:')
_,_,_,pred = match_all(rs, products, mapping)
for p in sorted(pred.values(), key=lambda x:(x.grade,x.color,x.thick,x.width_token)):
    print(p.grade, p.color, p.thick, p.width_token, p.length_token)

print('\nANSWER KEY MISSING:')
answer=set()
with (fixture/'answer_key.csv').open(newline='',encoding='utf-8') as f:
    for row in csv.DictReader(f):
        answer.add((row['thick'].strip(),row['grade'].strip(),row['color'].strip(),row['width_token'].strip(),row['length_token'].strip()))

doc_thicks={k[0] for k in answer}
predicted_keys={(p.thick,p.grade,p.color,p.width_token,p.length_token) for p in pred.values() if p.thick in doc_thicks}
missing=answer-predicted_keys
for p in sorted(missing):
    print(p)
