"""python3 recompute.py ANONYMOUS_BUNDLE > recomputed.json"""
import csv
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import sys

bundle = Path(sys.argv[1])
verified = {}


def verify(path, expected):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    verified[str(path.relative_to(bundle))] = digest


for name, expected in json.loads((bundle / "input-sha256.json").read_text()).items():
    verify(bundle / name, expected)
for label in ("A", "B"):
    folder = bundle / "authors" / label
    for line in (folder / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split()
        verify(folder / name, expected)

offices = {}
with (bundle / "shared-input.csv").open(encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        i = row["client_id"]
        assert i not in offices
        monthly = D(row["revenue_90"]) / 3
        offices[i] = dict(city=row["city"], monthly=monthly, trend=D(row["revenue_trend"]),
                          p=D(row["p"]), margin=monthly * 12 * D(".35"),
                          cost=D(1500) + monthly * 2 * D(".10"))
assert len(offices) == 965


def expected(i, retention):
    cell = offices[i]
    return retention * cell["margin"] * cell["p"] - cell["cost"]


rates = [D(".3"), D(".5"), D(".7")]
trend = sorted(offices, key=lambda i: (offices[i]["trend"], i))[:3]
positive = {}
for rate in rates:
    positive[rate] = sorted((i for i in offices if expected(i, rate) > 0),
                            key=lambda i: (-expected(i, rate), i))
fixed = positive[D(".5")][:3]
plans = [(rate, name, ids) for rate in rates for name, ids in
         (("trend", trend), ("fixed", fixed), ("reselected", positive[rate][:3]))]

with (bundle / "shared-input.csv").open(encoding="utf-8", newline="") as f:
    outcomes = {row["client_id"]: int(row["churn"]) for row in csv.DictReader(f)}
assert set(outcomes.values()) == {0, 1}
summaries = []
for rate, name, ids in plans:
    cost = sum(offices[i]["cost"] for i in ids)
    slope_model = sum(offices[i]["margin"] * offices[i]["p"] for i in ids)
    slope_scenario = sum(offices[i]["margin"] * outcomes[i] for i in ids)
    summaries.append(dict(s=rate, policy=name, ids=ids, cost=cost, departures=sum(outcomes[i] for i in ids),
                          model_slope=slope_model, model_net=rate*slope_model-cost,
                          scenario_slope=slope_scenario, scenario_net=rate*slope_scenario-cost,
                          model_break_even=cost/slope_model,
                          scenario_break_even=cost/slope_scenario if slope_scenario else None))
result = dict(verified_sha256=verified, office_count=len(offices),
              positive_counts={str(s): len(positive[s]) for s in rates},
              offices={i: dict(**offices[i], churn=outcomes[i], expected_at_half=expected(i, D(".5")))
                       for i in trend+fixed}, summaries=summaries)
print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
