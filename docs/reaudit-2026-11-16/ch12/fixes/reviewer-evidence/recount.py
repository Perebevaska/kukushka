"""Recount frozen first attempts, cutoff facts and the student's receipts using only stdlib."""
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

here = Path(__file__).resolve().parent
chapter = here.parents[1]
student = chapter / "student"

def jsonl(p):
    return [json.loads(line) for line in p.read_text().splitlines()]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

files = json.loads((student / "SHA256SUMS.json").read_text())
mismatch = [name for name, expected in files.items() if sha(student / name) != expected]
assert not mismatch
by_id = defaultdict(list)
for row in jsonl(student / "initial-attempts.jsonl"):
    by_id[row["id"]].append(row)
feedback = [r for p in sorted(student.glob("*.feedback.jsonl")) for r in jsonl(p)]
facts = list(csv.DictReader((chapter / "technical/data-baseline/app_orders.csv").open()))
time_map = {r["datetime"][:13]:int(r["orders"]) for r in facts}
june = [time_map[f"2026-06-30 {hour}"] for hour in range(20,24)]
july = [time_map[f"2026-07-31 {hour}"] for hour in range(20,24)]
rows = list(csv.DictReader((student / "native-august-predictions.csv").open()))
work = [r for r in rows if 7 <= int(r["datetime"][11:13]) <= 22]
assert len(rows) == 744 and len(work) == 496
plans = {}
for policy in ("model","baseline","quantile"):
    def needed(value):
        return max(1, math.ceil(float(value)/6))
    difference = [needed(r[policy])-needed(r["fact"]) for r in work]
    minus = sum(max(0,-v) for v in difference)
    plus = sum(max(0,v) for v in difference)
    plans[policy] = dict(
        rmse=math.sqrt(sum((float(r[policy])-float(r["fact"]))**2 for r in rows)/len(rows)),
        coverage=sum(float(r[policy]) >= float(r["fact"]) for r in work),
        short_hours=sum(v<0 for v in difference),
        deficit=minus, extra=plus, loss_3_to_1=3*minus+plus)
out = dict(student_hashes=len(files),manifest_sha256=sha(student/"SHA256SUMS.json"), unique_ids=len(by_id),graded=sum(map(len,by_id.values())),
           grade_totals=dict(Counter(r["passed"] for seq in by_id.values() for r in seq)),
           initial_graded_pass=sum(v[0]["passed"] for v in by_id.values()), latest_pass=sum(v[-1]["passed"] for v in by_id.values()),
           transport=[r for r in feedback if "browserError" in r], hints=[r for r in feedback if "hint" in r],
           june20_to23=june,july20_to23=july,raw_hours=len(rows),working_hours=len(work),work_zero=sum(int(r["fact"])==0 for r in work),own_native=plans)
(here/"independent-recount.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
