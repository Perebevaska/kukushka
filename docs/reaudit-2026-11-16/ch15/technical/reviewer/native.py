"""Replay frozen programs with isolated files, using the exported card's public runtime."""
import hashlib, importlib.util, json, os, shutil, sys, tempfile
from pathlib import Path

d = Path(__file__).resolve().parent
repo = d.parents[4]
bundle = d.parent / "data-baseline"
frozen = json.loads((d / "frozen.json").read_text())
frozen.extend(json.loads((d / "supplement.json").read_text()))
phase = sys.argv[1] if len(sys.argv) > 1 else "before"
source = Path(sys.argv[2]) if len(sys.argv) > 2 else (d.parent / "baseline-export.json")
tasks = {t["id"]: t for t in json.loads(source.read_text()) if t["kind"] == "task"}
original = {t["id"]: t for t in json.loads((d.parent/"baseline-export.json").read_text()) if t["kind"]=="task"}
spec = importlib.util.spec_from_file_location("harness", repo / "site/assets/harness.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
out = []
for case in frozen:
    old, task = original[case['task']], tasks[case['task']]
    check = task['check'] if old['check']==case['check'] else case['check']
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        for filename in case["files"]:
            shutil.copyfile(bundle / filename, filename)
        result = h.run(case["code"], check, task['setup'])
        out.append(dict(name=case["name"], expected=case["should_pass"], checked=result["check"], error=result["error"], output=result["out"][-1000:]))
        os.chdir(repo)
    print(case["name"], out[-1]["checked"], flush=True)
(d / (phase+"-native.json")).write_text(json.dumps(dict(python=sys.version, export_sha=hashlib.sha256(source.read_bytes()).hexdigest(),results=out),ensure_ascii=False,indent=2)+'\n')
