import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

for path in glob.glob("src/study_with_ai/8_RAG파이프라인구축/*.ipynb"):
    print(f"===== {os.path.basename(path)} =====")
    notebook = json.load(open(path, encoding="utf-8-sig"))
    for index, cell in enumerate(notebook["cells"]):
        source = "".join(cell.get("source", [])).strip()
        if not source:
            continue
        if cell["cell_type"] == "markdown":
            source = " | ".join(source.splitlines())
            print(f"MD{index}: {source[:1600]}")
        else:
            lines = [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith("#")]
            print(f"CODE{index}: {' | '.join(lines[:12])[:1600]}")
