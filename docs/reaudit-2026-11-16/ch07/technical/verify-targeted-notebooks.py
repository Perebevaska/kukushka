"""Check the two changed cards through published %%task cells in fresh kernels."""
import copy
import json
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / "site/notebooks"
sys.path.insert(0, str(ROOT / "tools"))
from make_notebooks import _verdicts

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

targets = {"ch07/03-threshold/roc-plot", "ch07/09-project/pipe"}
published = nbformat.read(OUT / "ch07-practice.ipynb", as_version=4)
tasks = json.loads((OUT / "tasks/ch07.json").read_text())["tasks"]
results = []
for mode in ("solution", "starter"):
    cells = []
    for original in published.cells:
        if original.cell_type != "code":
            continue
        if not original.source.startswith("%%task "):
            if "%load_ext dsc" in original.source:
                cells.append(copy.deepcopy(original))
            continue
        key = original.source.split("\n", 1)[0].split(" ", 1)[1].strip()
        if key not in targets:
            continue
        cell = copy.deepcopy(original)
        if mode == "solution":
            cell.source = "%%task " + key + "\n" + tasks[key]["solution"]
        cell.metadata["audit_key"] = key
        cells.append(cell)
    notebook = nbformat.v4.new_notebook(cells=cells)
    NotebookClient(notebook, timeout=900, kernel_name="python3", allow_errors=True,
                   resources={"metadata": {"path": str(OUT)}}).execute()
    for cell in notebook.cells:
        key = cell.metadata.get("audit_key")
        if not key:
            continue
        verdicts, error, _ = _verdicts(cell)
        passed = bool(verdicts) and verdicts[-1].startswith("✓")
        expected = mode == "solution"
        assert not error and verdicts and passed == expected, (key, mode, error, verdicts)
        results.append({"id": key, "mode": mode, "passed": passed, "expected": expected,
                        "feedback": verdicts[-1]})
        print(mode, key, "expected verdict", flush=True)
assert len(results) == 4
(HERE / "targeted-notebooks.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2) + "\n")
