"""Create one audit-only day; never overwrite the four published datasets."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent / "audit-holdout-private"
WORK = Path("/private/tmp/kuch14round/holdout-generation")
SEED = 14016


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    HERE.mkdir(exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    published = sorted((ROOT / "site/data").glob("showcase*.npz"))
    before = {str(p.relative_to(ROOT)): digest(p) for p in published}
    policy = ROOT / "docs/reaudit-2026-11-16/ch14/student/project-freeze.json"
    model = policy.parent / "project-model.pkl"
    assert policy.exists() and model.exists(), "Student must freeze its policy first"
    generator = ROOT / "tools/gen_data.py"
    spec = importlib.util.spec_from_file_location("audit_generator", generator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = WORK
    module.gen_chapter14(SEED, variant="_audit")
    with np.load(WORK / "showcase_day_audit.npz") as day:
        keys = list(zip(day["time"].tolist(), day["slot"].tolist()))
        assert len(keys) == len(set(keys)) == 732
        np.savez_compressed(HERE / "frames.npz", **{
            key: day[key] for key in ("X", "time", "slot", "classes")
        })
        with (HERE / "labels.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time", "slot", "true"])
            writer.writerows(zip(day["time"], day["slot"], day["y"]))
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in published}
    manifest = {
        "seed": SEED,
        "role": "one fresh synthetic audit day, not a new course requirement",
        "selection": "one predeclared seed, no search across outcomes",
        "generator_sha256": digest(generator),
        "frames_sha256": digest(HERE / "frames.npz"),
        "labels_sha256": digest(HERE / "labels.csv"),
        "student_policy_sha256": digest(policy),
        "student_model_sha256": digest(model),
        "published_unchanged": before,
        "keys": 732,
        "disclosure": "Release frames first; release labels only after prediction freeze",
    }
    (HERE / "generation.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "published_unchanged"}))


if __name__ == "__main__":
    main()
