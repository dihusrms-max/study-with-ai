import csv
from pathlib import Path
import matplotlib.pyplot as plt

PRED = Path('output/gomgom-api-dev.csv')
LABEL = Path('../../../open/dev_labels.csv')
OUT = Path.home() / 'Desktop' / 'gemma4_dev200_validation_gomgom.png'
ITEMS = [f'v{i}' for i in range(1, 25)]

def rows(path):
    with path.open(encoding='utf-8', newline='') as f:
        return {r['id']: r for r in csv.DictReader(f)}

pred, gold = rows(PRED), rows(LABEL)
stats = []
for item in ITEMS:
    tp = fp = fn = 0
    for rid in sorted(set(pred) & set(gold)):
        p, a = int(pred[rid][item]), int(gold[rid][item])
        tp += p == 1 and a == 1
        fp += p == 1 and a == 0
        fn += p == 0 and a == 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    stats.append((item, tp, fp, fn, precision, recall, f1))
macro = sum(x[-1] for x in stats) / len(stats)

plt.rcParams['font.family'] = 'DejaVu Sans'
fig, ax = plt.subplots(figsize=(16, 18), dpi=150)
ax.axis('off')
ax.set_title(f'Gemma4 dev 200 validation (Macro F1 {macro:.6f})', fontsize=22, fontweight='bold', pad=20)
headers = ['Item', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F1']
data = [[item, str(tp), str(fp), str(fn), f'{p:.6f}', f'{r:.6f}', f'{f:.6f}']
        for item, tp, fp, fn, p, r, f in stats]
table = ax.table(cellText=data, colLabels=headers, cellLoc='center', loc='center',
                 colWidths=[0.12, 0.12, 0.12, 0.12, 0.18, 0.18, 0.18])
table.auto_set_font_size(False)
table.set_fontsize(14)
table.scale(1, 2.0)
for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor('#cfcfcf')
    if row == 0:
        cell.set_facecolor('#dbe7f5')
        cell.set_text_props(weight='bold')
    elif row % 2 == 0:
        cell.set_facecolor('#fafafa')
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, bbox_inches='tight')
print(OUT)
print(f'macro_f1={macro:.6f}')
