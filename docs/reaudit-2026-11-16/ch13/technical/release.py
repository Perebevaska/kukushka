"""Verify chapter 13 sources, published downloads, data and export as one release."""
import json
import re
import sys
from hashlib import sha256
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
export_path = Path(sys.argv[1])
rows = [r for r in json.loads(export_path.read_text()) if r["lesson"].startswith("ch13/")]
assert sum(r["kind"] == "task" for r in rows) == 65
(D / "technical/chapter-export.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
sources = sorted((ROOT / "content/ch13").glob("*.md"))
figures = set(re.findall(r"(?m)^::: figure ([\w-]+)", "\n".join(p.read_text() for p in sources)))
files = sources + sorted((ROOT / "site/ch13").glob("*.html"))
files += [ROOT / "content/figures" / (name + ".svg") for name in sorted(figures)]
files += [ROOT / "site/notebooks" / name for name in
          ("project-template.ipynb", "ch13-practice.ipynb", "tasks/ch13.json", "check_notebook.py")]
files += [ROOT / "site/notebooks/requirements.txt"]
files += [ROOT / "site/notebooks/extra" / name for name in ("ch13-pymorphy3.ipynb", "ch13-transformers.ipynb", "requirements-extra.txt")]
files += [ROOT / "tools" / name for name in ("build.py", "make_notebooks.py", "gen_data.py")]
files += [ROOT / "site/assets" / name for name in ("course.js", "lesson.js", "core.js", "harness.py")]
files += sorted((ROOT / "tools/checks").glob("ch13*.py"))
for page in ("index",):
    assert "../notebooks/project-template.ipynb" in (ROOT / f"site/ch13/{page}.html").read_text()
result = {
    "baseline": json.loads((D / "technical/baseline.json").read_text())["head"],
    "full_course_export_sha256": sha256(export_path.read_bytes()).hexdigest(),
    "chapter_snapshot_sha256": sha256((D / "technical/chapter-export.json").read_bytes()).hexdigest(),
    "export_counts": {kind: sum(r["kind"] == kind for r in rows) for kind in sorted({r["kind"] for r in rows})},
    "files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in files},
    "data": {name: sha256((ROOT / "site/data" / name).read_bytes()).hexdigest()
             for name in sorted({name for r in rows for name in r["files"]})},
}
(D / "technical/release.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items() if key != "files"}, ensure_ascii=False, indent=2))
