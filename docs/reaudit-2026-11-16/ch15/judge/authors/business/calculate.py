"""Run with Python 3 from any directory. The input digest identifies the frozen snapshot."""
import csv
import hashlib
from math import fsum
from pathlib import Path

folder = Path(__file__).resolve().parent
input_file = folder.parents[1] / "shared-input.csv"
assert hashlib.sha256(input_file.read_bytes()).hexdigest() == "bc5c52aecbd772edcfc006a2c9c87fa37faa894be172f5db818a36f901b50395"

with input_file.open(encoding="utf-8") as stream:
    offices = [
        (r["client_id"], r["city"], float(r["revenue_90"]) / 3,
         float(r["revenue_trend"]), float(r["p"]))
        for r in csv.DictReader(stream)
    ]
assert len(offices) == len({r[0] for r in offices}) == 965

def benefit(office, s, risk):
    return risk * s * .35 * 12 * office[2] - 1500 - .2 * office[2]

def queue(s):
    eligible = [r for r in offices if benefit(r, s, r[4]) > 0]
    return sorted(eligible, key=lambda r: (-benefit(r, s, r[4]), r[0]))[:3]

baseline = sorted(offices, key=lambda r: (r[3], r[0]))[:3]
original = queue(.5)
plans = {s: queue(s) for s in (.3, .5, .7)}

# Persist every selection before reading any observed outcome.
with (folder / "selection.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["policy", "s", "rank", "client_id", "city", "revenue_month_rub", "revenue_trend", "p", "expected_rub"])
    for s, revised in plans.items():
        for policy, group in [("trend", baseline), ("fixed", original), ("reselect", revised)]:
            for rank, r in enumerate(group, 1):
                writer.writerow([policy, s, rank, *r, benefit(r, s, r[4])])
with input_file.open(encoding="utf-8") as stream:
    outcomes = {r["client_id"]: int(r["churn"]) for r in csv.DictReader(stream)}
with (folder / "results.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["s", "policy", "office_ids", "count", "departures", "charge_rub", "expected_rub", "scenario_rub", "s_break_even_model", "s_break_even_scenario"])
    for s, revised in plans.items():
        print("s", s, "positive-benefit offices:", sum(benefit(r, s, r[4]) > 0 for r in offices))
        for policy, group in [("trend", baseline), ("fixed", original), ("reselect", revised)]:
            charge = fsum(1500 + .2 * r[2] for r in group)
            risks = [r[4] for r in group]
            labels = [outcomes[r[0]] for r in group]
            expected, scenario = [fsum(benefit(r, s, x) for r, x in zip(group, xs)) for xs in (risks, labels)]
            slopes = [fsum(x * .35 * 12 * r[2] for r, x in zip(group, xs)) for xs in (risks, labels)]
            writer.writerow([s, policy, " ".join(r[0] for r in group), len(group), sum(labels), charge,
                             expected, scenario, *(charge / k if k else "" for k in slopes)])
