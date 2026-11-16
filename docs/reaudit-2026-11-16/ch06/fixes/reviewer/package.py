"""Extract the actual site and notebook check independently and build executable cases."""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CH = HERE.parent.parent
ROOT = CH.parents[2]
phase = sys.argv[1]
crit = CH / "check-evidence"
web = {}
nb = {}
if phase == "before":
    web = json.loads((HERE/"before-web.json").read_text())
    nb = json.loads((HERE/"before-nb.json").read_text())
else:
    def published(path):
        if phase == "baseline":
            return subprocess.check_output(["git","show","5c4c2ef:"+path.relative_to(ROOT).as_posix()],cwd=ROOT,text=True)
        return path.read_text()
    for page in (ROOT/"site/ch06").glob("*.html"):
        match = re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>', published(page), re.S)
        if match:
            for t in json.loads(match[1])["tasks"]:
                web[page.stem+"/"+t["id"]] = t
    nb = {k.removeprefix("ch06/"):v for k,v in json.loads(published(ROOT/"site/notebooks/tasks/ch06.json"))["tasks"].items()}
cases = []
def add(id, key, expected, code, **kwargs):
    cases.append({"id":id,"key":key,"expected":expected,"code":code, **kwargs})
def solution(key):
    return web[key]["solution"]
critfile = "original" if phase in {"before","baseline"} else "revised"
for t in json.loads((crit/f"probes-{critfile}.json").read_text()):
    cases.append({k:v for k,v in t.items() if k in {"id","key","expected","code","file_variants","setup_append"}})
for t in json.loads((crit/"probes-acceptance.json").read_text()):
    if t["key"] in web:
        cases.append({k:v for k,v in t.items() if k in {"id","key","expected","code","file_variants","setup_append"}})
key = "09-project/top"
s = solution(key)
add("R01", key, False, s + "\nrisk.loc[risk.idxmin()] = float('nan')")
add("R02", key, True, s + "\ncurrent_risk = current_risk.sort_values(ascending=True)")
add("R03", key, False, s + "\ncurrent_ids = current_ids[1:] + current_ids[:1]")
add("R04", key, False, s + "\nrule_top_ids = top_ids.copy()")
key = "07-regression/fact-pred"
s = solution(key)
point = 'ax.scatter(pred, y_test, s=8, alpha=0.5)'
assert point in s
add("R05", key, True, s.replace(point, 'for mask in (pred < 40, pred >= 40):\n    ax.scatter(pred[mask], y_test.to_numpy()[mask], s=8, alpha=0.5)'))
add("R06", key, False, s.replace(point, point+'\nax.scatter(pred[:2], y_test.iloc[:2][::-1])'))
add("R07", key, True, s.replace(point, 'ax.scatter(pred[::-1], y_test.iloc[::-1], s=8, alpha=0.5)'))
add("R08", key, False, s.replace(point, 'ax.scatter(pred[::-1], y_test, s=8, alpha=0.5)'))
key = "09-project/prepare"
add("R09", key, False, solution(key)+"\ny_test = y_test.sort_index().set_axis(y_test.index)")
key = "09-project/final"
add("R10", key, False, solution(key)+"\nmodel.fit(X, y)")
key = "09-project/top"
add("R11",key,False,solution(key)+"\ncurrent_risk = current_risk.reset_index(drop=True)")
key = "08b-groups-speed/speed-table"
s = solution(key)
assert s.count("time.perf_counter()") >= 2
add("R12", key, True, "from time import perf_counter as seconds\n"+s.replace("time.perf_counter()","seconds()"))
if phase == "extra":
    cases = json.loads((CH/"check-addendum/probes-after.json").read_text())
    schema = next(t for t in json.loads((crit/"probes-acceptance.json").read_text()) if t["id"]=="A08")
    cases.append(schema)
    web[schema["key"]] = nb[schema["key"]] = {"setup":"","check":""}
keys = sorted({c["key"] for c in cases})
rows = {k:{side:{name:t[k].get(name,"") or "" for name in ("setup","check")} for side,t in (("web",web),("nb",nb))} for k in keys}
(HERE/f"{phase}-cases.json").write_text(json.dumps({"tasks":rows,"cases":cases},ensure_ascii=False))
