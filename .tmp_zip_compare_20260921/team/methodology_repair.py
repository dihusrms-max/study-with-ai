import csv
from pathlib import Path

src = Path('output/gomgom-api-dev.csv')
dst = Path('output/gomgom-api-dev-methodology.csv')
items = range(1, 25)
absence = {10, 11, 16, 18, 20}
changed = []
with src.open(encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fields = reader.fieldnames
for row in rows:
    for i in items:
        if i in absence:
            continue
        if row[f'v{i}'] == '1' and not row[f'e{i}'].strip():
            changed.append((row['id'], f'v{i}'))
            row[f'v{i}'] = '0'
            row[f'e{i}'] = ''
with dst.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f'changed={len(changed)}')
for rid, item in changed:
    print(rid, item)
print(dst)
