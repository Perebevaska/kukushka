"""Rebuild chapter 7 inventory and actual submission coverage from saved files."""
import json
import re
from collections import Counter
from hashlib import sha256
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
inventory = {}
for path in sorted((ROOT / "content/ch07").glob("*.md")):
    text = path.read_text()
    for task in re.findall(r"^## task: ([\w-]+)\s*\|", text, re.M):
        inventory[f"{path.stem}/{task}"] = "task"
    for kind in ("predict", "quiz"):
        for n, _ in enumerate(re.finditer(r"^::: " + kind + r"\b", text, re.M), 1):
            inventory[f"{path.stem}/{kind}/{n}"] = "final_quiz" if path.stem == "test" else kind

def read(name):
    path = D / "student" / name
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []

def stats(rows):
    latest = {}
    for row in rows:
        latest[row["id"]] = row["passed"]
    return {
        "submissions": len(rows),
        "distinct_ids": len(latest),
        "passed": sum(r["passed"] is True for r in rows),
        "failed": sum(r["passed"] is False for r in rows),
        "expect_before_answer": sum(bool(r.get("expect")) for r in rows),
        "latest_failed": [key for key, value in latest.items() if value is not True],
        "ids": sorted(latest),
    }

initial = read("initial-attempts.jsonl")
retest = read("retest-attempts.jsonl")
latest = {}
history = {}
for phase, rows in (("initial", initial), ("retest", retest)):
    for line, row in enumerate(rows, 1):
        latest[row["id"]] = row["passed"]
        history.setdefault(row["id"], []).append({"file": phase + "-attempts.jsonl", "line": line, "passed": row["passed"]})
target_path = D / "technical/retest-targets.json"
targets = json.loads(target_path.read_text()) if target_path.exists() else []
data = {
    "inventory": dict(Counter(inventory.values())),
    "initial": stats(initial), "retest": stats(retest),
    "missing_initial": sorted(set(inventory) - {r["id"] for r in initial}),
    "missing_or_failed_final": [key for key in inventory if latest.get(key) is not True],
    "unknown": sorted(set(latest) - set(inventory)),
    "missing_retest": sorted(set(targets) - {r["id"] for r in retest}),
    "targets": targets,
    "history": history,
    "sources": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                for path in sorted((ROOT / "content/ch07").glob("*.md"))},
}
(D / "coverage.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: value for key, value in data.items() if key not in ("history", "sources")}, ensure_ascii=False, indent=2))
