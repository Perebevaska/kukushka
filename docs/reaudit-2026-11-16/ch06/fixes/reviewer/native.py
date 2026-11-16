import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
import sklearn, pandas, time
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

def timer_methods():
    return (time.perf_counter, *(getattr(cls, name) for cls in (DecisionTreeClassifier,RandomForestClassifier,LogisticRegression) for name in ("fit","predict")))


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0,str(ROOT/"site/assets"))
import harness
phase = sys.argv[1]
evidence = HERE.parent.parent/"check-evidence"
base = evidence/"data-baseline"
data = base if phase in {"before","baseline"} else ROOT/"site/data"
batch = json.loads((HERE/f"{phase}-cases.json").read_text())
with tempfile.TemporaryDirectory() as folder, (HERE/f"{phase}-nb.jsonl").open("w") as log:
    os.chdir(folder)
    print(json.dumps({"python":sys.version,"sklearn":sklearn.__version__,"pandas":pandas.__version__}),file=log)
    for c in batch["cases"]:
        for f in base.glob("*.csv"):
            src = evidence/c["file_variants"][f.name] if f.name in c.get("file_variants",{}) else data/f.name
            shutil.copyfile(src,f.name)
        t = batch["tasks"][c["key"]]["nb"]
        originals = timer_methods()
        r = harness.run(c["code"], t["check"], t["setup"]+"\n"+c.get("setup_append",""))
        restored = all(old is new for old,new in zip(originals,timer_methods()))
        assert restored, c["id"]
        if phase in {"after","extra"}:
            assert r["check"]["passed"]==c["expected"], (c["id"],r["check"])
        print(json.dumps(dict(timer_and_methods_restored=restored,id=c["id"],key=c["key"],expected=c["expected"],observed=r["check"]["passed"],msg=r["check"]["msg"],error=r["error"]),ensure_ascii=False),file=log,flush=True)
