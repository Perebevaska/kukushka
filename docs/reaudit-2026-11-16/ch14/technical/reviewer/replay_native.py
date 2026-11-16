import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

base = Path(__file__).resolve().parent
checks = base.parent / "checks"
phase = sys.argv[1]
tasks_file = Path(sys.argv[2]) if len(sys.argv) > 2 else checks / "tasks.json"
digest = lambda data: hashlib.sha256(data).hexdigest()
program_bytes = (base / "programs.jsonl").read_bytes()
freeze = json.loads((base / "freeze.json").read_text())
assert digest(program_bytes) == freeze["programs_sha256"]
tasks = {(t["lesson"], t["id"]): t for t in json.loads(tasks_file.read_text())}
spec = importlib.util.spec_from_file_location("harness", checks / "frozen_harness.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
entries = []
with tempfile.TemporaryDirectory() as scratch:
    os.chdir(scratch)
    os.environ["MPLCONFIGDIR"] = scratch
    for row in map(json.loads, program_bytes.splitlines()):
        task = tasks[row["lesson"], row["task"]]
        for name in task["files"]:
            Path(name).write_bytes((checks / "data" / name).read_bytes())
        result = harness.run(row["code"], task["check"], task["setup"], bool(task.get("display")))
        entries.append(dict(name=row["name"], expected=row["expected"], passed=result["check"]["passed"],
                            ok=result["ok"], message=result["check"]["msg"], error=result["error"],
                            figureCount=len(result["figs"]), code_sha256=row["sha256"]))
        print(row["name"], entries[-1]["passed"], flush=True)
(base / (phase + "-native.json")).write_text(json.dumps(dict(
    runtime=sys.version, executed_utc=datetime.now(timezone.utc).isoformat(),
    task_sha256=digest(tasks_file.read_bytes()), programs_sha256=digest(program_bytes),
    entries=entries), ensure_ascii=False, indent=2))
