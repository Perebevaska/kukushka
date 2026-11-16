"""Recipient-side verification. Run only after the CPU window is released.

Uses the snapshotted handoff, never edits student/project. Saved-model inference
is executed first, before the separately labelled notebook retraining check.
"""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

EVIDENCE = Path(__file__).resolve().parent
INPUTS = EVIDENCE / "first-inputs"
PYTHON = Path("/private/tmp/ku-audit/nb-env/bin/python")
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def compare(actual_path, expected_path):
    actual, expected = read_csv(actual_path), read_csv(expected_path)
    key = lambda row: (row["date"], row["shop_id"])
    amap, emap = {key(r): r for r in actual}, {key(r): r for r in expected}
    assert len(amap) == len(actual), "duplicate actual keys"
    assert len(emap) == len(expected), "duplicate expected keys"
    assert amap.keys() == emap.keys(), "different date/shop key sets"
    diffs = [abs(float(amap[k]["prediction_k"]) - float(emap[k]["prediction_k"])) for k in amap]
    assert all(math.isfinite(x) and x <= 1e-9 for x in diffs), "prediction mismatch"
    return {"rows": len(actual), "unique_keys": len(amap), "max_abs_difference_k": max(diffs, default=0),
            "tolerance_k": 1e-9, "min_date": min(k[0] for k in amap), "max_date": max(k[0] for k in amap)}


def copy_project(target):
    shutil.copytree(INPUTS, target)
    (target / "public-daily-sales.csv").unlink()
    return target


def command(work, args, name):
    cmd = [str(PYTHON), *args]
    run = subprocess.run(cmd, cwd=work, env=ENV, capture_output=True, text=True, timeout=180)
    (EVIDENCE / (name + ".log")).write_text("COMMAND " + json.dumps(cmd) + "\nCWD " + str(work) + "\n" + run.stdout + "\nSTDERR\n" + run.stderr)
    assert run.returncode == 0, f"{name}: exit {run.returncode}; see log"
    return {"command": cmd, "cwd": str(work), "exit_code": run.returncode, "log": name + ".log"}


def main():
    workroot = Path(tempfile.mkdtemp(prefix="ch10-recipient-"))
    result = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "workroot": str(workroot),
              "input_manifest": "first-inputs-manifest.json", "ordered_checks": []}
    (EVIDENCE / "verification-start.json").write_text(json.dumps(result, indent=2))
    base = copy_project(workroot / "saved-model")
    before_model = digest(base / "model.joblib")
    step = command(base, ["run.py", "--predict", "request.csv", "--output", "recipient-recomputed.csv"], "saved-model")
    step.update(compare(base / "recipient-recomputed.csv", base / "plan.csv"))
    step.update(model_sha256_before=before_model, model_sha256_after=digest(base / "model.joblib"), retrained=False)
    assert step["model_sha256_before"] == step["model_sha256_after"]
    request = read_csv(base / "request.csv")
    assert len(request) == 1104
    assert len(set(r["shop_id"] for r in request)) == 6
    assert len(set(r["date"] for r in request)) == 184
    step["request_columns"] = list(request[0])
    step["request_has_target_or_weather"] = any(c in request[0] for c in ["revenue_k", "temp", "rain"])
    assert not step["request_has_target_or_weather"]
    result["ordered_checks"].append({"saved_model": step})
    shutil.copy2(base / "recipient-recomputed.csv", EVIDENCE / "saved-model-recomputed.csv")

    # A different requested period uses only the documented saved-model CLI.
    # This is an October--December subset of the July-issued model, not a claim
    # that the package can issue a newly trained October model.
    alternate = [r for r in request if r["date"] >= "2025-10-01"]
    write_csv(base / "request-q4.csv", alternate)
    expected = [r for r in read_csv(base / "plan.csv") if r["date"] >= "2025-10-01"]
    write_csv(base / "expected-q4.csv", expected)
    step = command(base, ["run.py", "--predict", "request-q4.csv", "--output", "recipient-q4.csv"], "alternate-period")
    step.update(compare(base / "recipient-q4.csv", base / "expected-q4.csv"))
    step.update(model_issue_date="2025-07-01", requested_period_start="2025-10-01", newly_issued_model=False)
    result["ordered_checks"].append({"alternate_period": step})

    write_csv(base / "single-request.csv", request[:1])
    write_csv(base / "single-expected.csv", read_csv(base / "plan.csv")[:1])
    step = command(base, ["run.py", "--predict", "single-request.csv", "--output", "single-result.csv"], "single-row")
    step.update(compare(base / "single-result.csv", base / "single-expected.csv"))
    result["ordered_checks"].append({"single_row": step})
    write_csv(base / "shuffled-request.csv", request[::-1])
    step = command(base, ["run.py", "--predict", "shuffled-request.csv", "--output", "shuffled-result.csv"], "shuffled-rows")
    step.update(compare(base / "shuffled-result.csv", base / "plan.csv"))
    result["ordered_checks"].append({"shuffled_rows": step})

    # Independently mutate unavailable revenue and weather on/after the July
    # issue date. The saved model has no reason to access this training CSV.
    modified = copy_project(workroot / "modified-future")
    raw = read_csv(modified / "data/daily_sales.csv")
    affected = 0
    for row in raw:
        if row["date"] >= "2025-07-01":
            row.update(revenue_k="999999", temp="12345", rain="98765")
            affected += 1
    write_csv(modified / "data/daily_sales.csv", raw)
    step = command(modified, ["run.py", "--predict", "request.csv", "--output", "after-future-mutation.csv"], "saved-model-future-mutation")
    step.update(compare(modified / "after-future-mutation.csv", base / "plan.csv"))
    step.update(mutated_rows=affected, cutoff="2025-07-01", mutated_columns=["revenue_k", "temp", "rain"], retrained=False)
    result["ordered_checks"].append({"saved_model_future_mutation": step})

    # Only now execute the handed-off notebook from a clean kernel, explicitly
    # classifying this as the package's separate retraining entry point.
    notebook = copy_project(workroot / "notebook-clean-kernel")
    code = ("from pathlib import Path; import nbformat; from nbclient import NotebookClient; "
            "p=Path('project.ipynb'); n=nbformat.read(p,as_version=4); "
            "[c.update(outputs=[]) for c in n.cells if c.cell_type=='code']; "
            "[c.update(execution_count=None) for c in n.cells if c.cell_type=='code']; "
            "NotebookClient(n,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(Path.cwd())}}).execute(); "
            "nbformat.write(n,'recipient-executed.ipynb')")
    step = command(notebook, ["-c", code], "clean-notebook-retraining")
    step.update(compare(notebook / "plan.csv", base / "plan.csv"))
    step["retrained"] = True
    step["actual_versions"] = json.loads((notebook / "versions.json").read_text())
    step["selection"] = json.loads((notebook / "selection.json").read_text())
    result["ordered_checks"].append({"clean_notebook_retraining": step})
    shutil.copy2(notebook / "recipient-executed.ipynb", EVIDENCE / "recipient-executed.ipynb")
    shutil.copy2(notebook / "metrics.csv", EVIDENCE / "clean-notebook-metrics.csv")

    # A separate, clearly labelled full regeneration on changed future facts
    # checks the training boundary rather than merely independence of reload.
    step = command(modified, ["run.py"], "retraining-future-mutation")
    step.update(compare(modified / "plan.csv", base / "plan.csv"))
    selection = json.loads((modified / "selection.json").read_text())
    original_selection = json.loads((INPUTS / "selection.json").read_text())
    assert selection["chosen"] == original_selection["chosen"]
    assert [(r["model"], r["val_rmse_k"]) for r in selection["rows"]] == [(r["model"], r["val_rmse_k"]) for r in original_selection["rows"]]
    step.update(mutated_rows=affected, cutoff="2025-07-01", retrained=True, chosen=selection["chosen"], validation_rmse_unchanged=True)
    result["ordered_checks"].append({"retraining_future_mutation": step})
    result["first_author_knowledge_needed"] = None
    result["alternate_release_limitation"] = "README/run.py expose no as-of option; alternate period uses the unchanged July-issued model. Issuing a newly trained October model would require undocumented source edits."
    (EVIDENCE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
