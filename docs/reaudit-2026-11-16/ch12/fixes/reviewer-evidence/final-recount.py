"""Independent stdlib-only reconciliation of the three submissions and hourly forecasts."""
from pathlib import Path
from datetime import datetime, timedelta
import csv
import hashlib
import json
from math import ceil, sqrt

here = Path(__file__).resolve().parent
chapter = here.parents[1]
root = here.parents[4]
first = chapter / "student"
retake = chapter / "fixes/student/retest"
last = chapter / "fixes/student/decision-closure"

def read(path):
    return json.loads(path.read_text())

def rows(path):
    with path.open() as file:
        return list(csv.DictReader(file))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]

verified = {}
for stage, folder in [("first",first),("retake",retake),("decision",last)]:
    manifest = folder / "SHA256SUMS.json"
    entries = read(manifest)
    assert all(sha(folder/k)==v for k,v in entries.items())
    verified[stage] = dict(count=len(entries),sha256=sha(manifest))
out = dict(manifests=verified)
feedback = [r for p in retake.glob("*.feedback.jsonl") for r in jsonl(p)]
ids = [r["id"] for r in feedback]
targets = read(retake/"targets.json")["targets"]
target_ids={r if isinstance(r,str) else r["id"] for r in targets}
assert len(ids)==len(set(ids))==47 and set(ids)==target_ids
assert all(r["passed"] is True for r in feedback)
closure = jsonl(last/"quiz.feedback.jsonl")
assert len(closure)==1 and closure[0]["id"] in ids and closure[0]["passed"] is True
out["submissions"] = dict(retake=len(ids),unique_retakes=len(set(ids)),passed=len(ids), closure_id=closure[0]["id"],extra_passed=1,unique_ids_after_closure=len(set(ids)|{closure[0]["id"]}))
metrics = rows(retake/"native-august-predictions.csv")
by_ts = {r["datetime"]:r for r in metrics}
prior={r["datetime"]:r for r in rows(first/"native-august-predictions.csv")}
calendar_diff = [t for t,r in by_ts.items() if float(prior[t]["model"])!=float(r["model"])]
assert calendar_diff==[f"2026-08-21 {h:02}:00:00" for h in range(10,21)]
work = [r for r in metrics if 7<=int(r["datetime"][11:13])<=22]
assert len(by_ts)==len(metrics)==744 and len(work)==496
out["changed_predictions"]=calendar_diff
out["plans"] = {}
for k in ["model","baseline","quantile"]:
    diffs=[max(1,ceil(float(r[k])/6))-max(1,ceil(float(r["fact"])/6)) for r in work]
    d=sum(max(0,-x) for x in diffs); e=sum(max(0,x) for x in diffs)
    rmse=lambda rs:sqrt(sum((float(r[k])-float(r["fact"]))**2 for r in rs)/len(rs))
    out["plans"][k] = dict(all_hours=len(metrics),work_hours=len(work),all_rmse=rmse(metrics),work_rmse=rmse(work),short=sum(x<0 for x in diffs),covered_work=sum(float(r[k])>=float(r["fact"]) for r in work),deficit=d,extra=e,cost_3_1=3*d+e)
seen=set()
paths=sorted((retake/"issued").glob("*.csv"))
for p in paths:
    issue=datetime.fromisoformat(p.stem)-timedelta(hours=4)
    day=rows(p)
    assert len(day)==24
    for i,r in enumerate(day):
        assert set(r)=={"","model","quantile","baseline","cutoff","issue"}
        ts=r[""]; assert ts not in seen and datetime.fromisoformat(ts)==datetime.fromisoformat(p.stem)+timedelta(hours=i)
        assert datetime.fromisoformat(r["issue"])==issue and datetime.fromisoformat(r["cutoff"])==issue-timedelta(hours=1)
        assert all(float(r[k])==float(by_ts[ts][k]) for k in ["model","baseline","quantile"])
        seen.add(ts)
assert seen==set(by_ts) and len(paths)==31
out["batches"]=dict(files=len(paths),target_hours=len(seen),pre_fact_forecast_values=len(seen)*3)
cost={}
for c in [6,5]:
    needs=[max(1,ceil(y/c)) for y in [13,0,11]]
    cost[c]={staff:sum(180*max(0,n-staff)+100*max(0,staff-n) for n in needs) for staff in [2,3]}
assert cost=={6:{2:280,3:300},5:{2:460,3:200}}
out["capacity_only"]=cost
release=read(chapter/"technical/release.json")
assert all(sha(root/k)==v for k,v in release["files"].items())
assert all(sha(root/"site/data"/k)==v for k,v in release["data"].items())
out["actual_release"]=dict(files=len(release["files"]),datasets=len(release["data"]),export=release["full_course_export_sha256"])
out["letter_sha"]=sha(last/"manager-letter.md")
(here/"final-recount.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
