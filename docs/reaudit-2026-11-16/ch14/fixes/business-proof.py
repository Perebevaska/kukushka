#!/usr/bin/env python3
"""Independent replay. Use the course environment and redirect stdout to a new JSON."""
import csv
import hashlib
import json
import os
import pickle
from datetime import datetime
from itertools import groupby
from pathlib import Path

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[name] = "1"
import numpy as np
import sklearn

chapter = Path(__file__).resolve().parents[1]
repo = chapter.parents[2]
initial = chapter / "student"
private = chapter / "technical" / "audit-holdout-private"
submissions = chapter / "fixes" / "student" / "holdout-predictions"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    return json.loads(path.read_text())

def verify_manifest(directory):
    lines = (directory / "SHA256SUMS").read_text().splitlines()
    paths = set()
    for line in lines:
        expected, name = line.split("  ", 1)
        assert name not in paths and digest(directory / name) == expected, name
        paths.add(name)
    return len(paths)

def csv_keys(path, field=None):
    with path.open() as src:
        rows = list(csv.DictReader(src))
    pairs = [(row["time"], int(row["slot"])) for row in rows]
    assert len(set(pairs)) == len(rows), path
    if field is None:
        return set(pairs)
    return {key: int(row[field]) for key, row in zip(pairs, rows)}

times = [f"{m // 60:02d}:{m % 60:02d}" for m in range(420, 1321, 15)]
all_keys = {(t, s) for t in times for s in range(12)}

def events(truth, pred, k, prices):
    assert truth.keys() == pred.keys() == all_keys
    signals = set()
    episodes = []
    for slot in range(12):
        for empty, group in groupby(times, key=lambda t: pred[t, slot] == 0):
            run = list(group)
            if empty and len(run) >= k:
                signals.add((run[k - 1], slot))
        for empty, group in groupby(times, key=lambda t: truth[t, slot] == 0):
            run = list(group)
            if empty:
                hits = [t for t in run if (t, slot) in signals]
                episodes.append(dict(slot=slot, start=run[0], end=run[-1], hits=hits,
                                     delay=15 * run.index(hits[0]) if hits else None))
    delays = [e["delay"] for e in episodes if e["hits"]]
    missed = len(episodes) - len(delays)
    false = sum(truth[key] != 0 for key in signals)
    repeated = sum(max(0, len(e["hits"]) - 1) for e in episodes)
    cost = prices["false"] * false + prices["missed"] * missed + prices["repeated"] * repeated + prices["delay_minute"] * sum(delays)
    metrics = dict(n_alerts=len(signals), false=false, missed=missed, repeated=repeated,
                   n_episodes=len(episodes), delay_total=sum(delays),
                   delay_minutes=sum(delays) / len(delays) if delays else None, cost=cost)
    return signals, episodes, metrics

generation = read_json(private / "generation.json")
release = read_json(private / "labels-disclosure.json")
policy = read_json(initial / "project-freeze.json")
policy_stamp = read_json(initial / "freeze-before-day2.json")
pred_stamp = read_json(submissions / "freeze.json")
assert verify_manifest(initial) == 59 and verify_manifest(submissions) == 10
for path, expected_hash in generation["published_unchanged"].items():
    assert digest(repo / path) == expected_hash
assert digest(repo / "tools/gen_data.py") == generation["generator_sha256"]
assert digest(initial / "project-freeze.json") == generation["student_policy_sha256"] == policy_stamp["sha256"]
assert digest(initial / "project-model.pkl") == generation["student_model_sha256"]
assert digest(private / "frames.npz") == generation["frames_sha256"]
assert digest(private / "labels.csv") == generation["labels_sha256"] == release["labels_sha256"]
assert digest(submissions / "SHA256SUMS") == release["prediction_manifest_sha256"]
for name, value in pred_stamp["sha256"].items():
    assert digest(submissions / name) == value
timestamps = [policy_stamp["utc"], pred_stamp["utc"], release["released_at"]]
assert sorted(map(datetime.fromisoformat, timestamps)) == list(map(datetime.fromisoformat, timestamps))
assert generation["seed"] == 14016 and policy["chosen_k"] == 2 and not pred_stamp["labels_available"]
with (initial / "project-model.pkl").open("rb") as src:
    model = pickle.load(src)
assert model.n_estimators == 100 and model.n_jobs == 1 and model.random_state == 0
with np.load(private / "frames.npz") as data:
    assert set(data.files) == {"time", "slot", "X", "classes"}
    keys = list(zip(data["time"].astype(str).tolist(), data["slot"].astype(int).tolist()))
    assert len(keys) == 732 and set(keys) == all_keys
    pixels = data["X"].reshape(732, -1) / 255
    norm = (pixels - pixels.mean(axis=1)[:, None]) / (pixels.std(axis=1)[:, None] + 1e-8)
    raw = dict(zip(keys, model.predict(norm).astype(int).tolist()))
assert raw == csv_keys(submissions / "predictions.csv", "pred")
truth = csv_keys(private / "labels.csv", "true")
signals, episodes, metrics = events(truth, raw, policy["chosen_k"], policy["prices"])
assert signals == csv_keys(submissions / "signals.csv")

project = {}
for day, thresholds in [(1, (1, 2, 3)), (2, (policy["chosen_k"],))]:
    path = initial / f"project-day{day}.csv"
    with np.load(repo / "site/data" / ("showcase_day.npz" if day == 1 else "showcase_day_next.npz")) as data:
        day_truth = dict(zip(zip(data["time"].tolist(), data["slot"].tolist()), data["y"].tolist()))
    assert day_truth == csv_keys(path, "true")
    project[day] = {k: events(day_truth, csv_keys(path, "pred"), k, policy["prices"])[2] for k in thresholds}
assert all(policy["policy_table"][str(k)] == m for k, m in project[1].items())
assert policy["chosen_k"] == min(project[1], key=lambda k: (project[1][k]["cost"], k))
right = sum(raw[key] == truth[key] for key in keys)
evening_right = sum(raw[key] == truth[key] for key in keys if key[0] >= "18:00")
print(json.dumps(dict(sklearn=sklearn.__version__, numpy=np.__version__, timestamps_utc=timestamps,
                      frozen_files=[59, 10], published_npz_match=4, original_project=project,
                      matching_predictions=len(raw), matching_signals=len(signals),
                      correct_classes=right, correct_evening=evening_right,
                      holdout=metrics, episodes=episodes,
                      false_alert_keys=sorted(key for key in signals if truth[key] != 0)),
                 ensure_ascii=False, indent=2))
