"""Independent second handoff receipt; executes only supplied documented CLI.

One extra profiled repetition observes saved-mode methods without modifying the
handed-off source. No notebook execution or model selection is performed here.
"""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from verify_receipt import compare, read_csv, write_csv, digest

E = Path(__file__).resolve().parent
SOURCE = E / "second-inputs"
PYTHON = "/private/tmp/ku-audit/nb-env/bin/python"
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def main():
    workroot = Path(tempfile.mkdtemp(prefix="ch10-recipient-second-"))
    project = workroot / "project"
    shutil.copytree(SOURCE, project)
    out = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "workroot": str(workroot),
           "inputs": "second-inputs-manifest.json", "independent_date_precommitted": "first-receipt2.json",
           "checks": [], "commands": [], "notebook_rerun": False, "threads": 1}

    def run(args, label):
        cmd = [PYTHON, "run.py", *args]
        result = subprocess.run(cmd, cwd=project, env=ENV, capture_output=True, text=True, timeout=180)
        (E / ("second-" + label + ".log")).write_text("COMMAND " + json.dumps(cmd) + "\nCWD " + str(project) + "\n" + result.stdout + "\nSTDERR\n" + result.stderr)
        out["commands"].append({"label": label, "command": cmd, "exit_code": result.returncode})
        assert result.returncode == 0, (label, result.stderr)

    def check(actual, expected, as_of, label):
        c = compare(project / actual, project / expected)
        rows = read_csv(project / actual)
        assert {r["as_of"] for r in rows} == {as_of}
        assert all(r["date"] >= as_of for r in rows)
        c.update(label=label, as_of=as_of)
        out["checks"].append(c)
        return c

    def saved(model, metadata, request, output, label):
        before = digest(project / model)
        run(["saved", "--model", model, "--metadata", metadata, "--request", request, "--output", output], label)
        after = digest(project / model)
        assert before == after
        return {"model_sha256_before": before, "model_sha256_after": after}

    original_hash = digest(project / "model.joblib")
    # Demonstrate that the first documented saved command needs no training CSV.
    shutil.move(str(project / "data"), str(workroot / "temporarily-unavailable-data"))
    s = saved("model.joblib", "metadata.json", "request.csv", "recipient-july.csv", "saved-july")
    c = check("recipient-july.csv", "plan.csv", "2025-07-01", "handed July model without training data")
    c.update(s, training_data_present=False)
    shutil.move(str(workroot / "temporarily-unavailable-data"), str(project / "data"))

    # Observe which relevant methods are called. This extra diagnostic executes
    # the same argv via runpy, after the plain documented command passed.
    profile_code = '''import sys,runpy,json
from pathlib import Path
calls={}
def trace(frame,event,arg):
    if event!='call': return
    fn=frame.f_code.co_filename; name=frame.f_code.co_name
    if (Path(fn).name=='run.py' or '/sklearn/' in fn or '/joblib/' in fn) and name in {'fit','partial_fit','predict','load','plan_frame','features','make_issue'}:
        key=fn+':'+name;calls[key]=calls.get(key,0)+1
sys.argv=['run.py','saved','--model','model.joblib','--metadata','metadata.json','--request','request.csv','--output','profiled-july.csv']
sys.setprofile(trace)
runpy.run_path('run.py',run_name='__main__')
sys.setprofile(None)
Path('saved-method-calls.json').write_text(json.dumps(calls,indent=2))
'''
    diagnostic = subprocess.run([PYTHON, "-c", profile_code], cwd=project, env=ENV, capture_output=True, text=True, timeout=180)
    assert diagnostic.returncode == 0, diagnostic.stderr
    calls = json.loads((project / "saved-method-calls.json").read_text())
    assert not any(k.endswith(':fit') or k.endswith(':partial_fit') or k.endswith(':make_issue') for k in calls)
    assert digest(project / "model.joblib") == original_hash
    out["saved_mode_method_observation"] = {"methods": calls, "fit_calls": 0, "make_issue_calls": 0, "source_modified": False}
    shutil.copy2(project / "saved-method-calls.json", E / "second-saved-method-calls.json")

    # First reproduce the newly supplied September-trained bundle itself.
    s = saved("new-issue.joblib", "new-issue.json", "new-request.csv", "recipient-september-handed.csv", "saved-handed-september")
    check("recipient-september-handed.csv", "new-plan.csv", "2025-09-01", "handed September model reload").update(s)

    def issue(as_of, request, stem, history="data/daily_sales.csv", verify=False):
        args = ["issue", "--as-of", as_of, "--history", history, "--request", request,
                "--output", stem + ".csv", "--model-out", stem + ".joblib", "--metadata-out", stem + ".json"]
        if verify:
            args.append("--verify-future-invariance")
        run(args, stem)
        m = json.loads((project / (stem + ".json")).read_text())
        assert m["as_of"] == as_of and m["last_available_observation"] < as_of
        assert m["units"] == "thousand RUB per shop-day"
        assert m["recipe"] == {"name":"trend_hgb","max_iter":200,"max_depth":3,"learning_rate":.05,"random_state":11,"weather":"excluded","origin":"2024-01-01"}
        assert m["threads"] == 1
        req = read_csv(project / request)
        plan = read_csv(project / (stem + ".csv"))
        key = lambda r: (r["date"],r["shop_id"])
        assert len(req) == len(plan) and {key(r) for r in req} == {key(r) for r in plan}
        assert len({key(r) for r in plan}) == len(plan)
        out.setdefault("issue_key_checks", []).append({"issue": stem, "request_rows": len(req), "output_rows": len(plan), "exact_request_key_match": True})
        out.setdefault("issue_metadata", {})[stem] = m
        shutil.copy2(project / (stem + ".json"), E / ("second-" + stem + ".json"))
        return m

    m = issue("2025-09-01", "new-request.csv", "recipient-september", verify=True)
    assert m["history_rows"] == 3654 and m["last_available_observation"] == "2025-08-31"
    check("recipient-september.csv", "new-plan.csv", "2025-09-01", "new September issue")
    saved("recipient-september.joblib", "recipient-september.json", "new-request.csv", "recipient-september-reloaded.csv", "saved-regenerated-september")
    check("recipient-september-reloaded.csv", "recipient-september.csv", "2025-09-01", "regenerated September reload")

    # This date/horizon was chosen in first-receipt2 before reading the source.
    request = [r for r in read_csv(project / "request.csv") if r["date"] >= "2025-10-01"]
    assert len(request) == 552
    write_csv(project / "recipient-october-request.csv", request)
    shutil.copy2(project / "recipient-october-request.csv", E / "second-october-request.csv")
    m = issue("2025-10-01", "recipient-october-request.csv", "recipient-october", verify=True)
    assert m["history_rows"] == 3834 and m["last_available_observation"] == "2025-09-30"
    assert m["horizon_start"] == "2025-10-01" and m["horizon_end"] == "2025-12-31"
    saved("recipient-october.joblib", "recipient-october.json", "recipient-october-request.csv", "recipient-october-reloaded.csv", "saved-october")
    check("recipient-october-reloaded.csv", "recipient-october.csv", "2025-10-01", "independent October issue reload")
    shutil.copy2(project / "recipient-october.csv", E / "second-october-plan.csv")

    # Independent external mutation, not only the package's own mutation flag.
    rows = read_csv(project / "data/daily_sales.csv")
    affected = 0
    for r in rows:
        if r["date"] >= "2025-10-01":
            r.update(revenue_k="999999", temp="12345", rain="98765")
            affected += 1
    assert affected == 552
    write_csv(project / "recipient-mutated-future.csv", rows)
    issue("2025-10-01", "recipient-october-request.csv", "recipient-october-mutated", history="recipient-mutated-future.csv")
    c = check("recipient-october-mutated.csv", "recipient-october.csv", "2025-10-01", "independent future mutation")
    c.update(mutated_rows=affected, mutated_columns=["revenue_k", "temp", "rain"], unchanged_calendar_and_request=True)

    # An operational input with no future rows at all must issue the same plan.
    history_only = [r for r in read_csv(project / "data/daily_sales.csv") if r["date"] < "2025-10-01"]
    write_csv(project / "recipient-october-history-input.csv", history_only)
    issue("2025-10-01", "recipient-october-request.csv", "recipient-october-history-only", history="recipient-october-history-input.csv")
    check("recipient-october-history-only.csv", "recipient-october.csv", "2025-10-01", "history-only input")

    # Check that predictions do not depend on the remainder/order of the batch.
    expected = read_csv(project / "recipient-october.csv")
    write_csv(project / "one.csv", request[-1:])
    write_csv(project / "one-expected.csv", expected[-1:])
    saved("recipient-october.joblib", "recipient-october.json", "one.csv", "one-out.csv", "october-single")
    check("one-out.csv", "one-expected.csv", "2025-10-01", "single last row")
    group = [r for r in request if r["date"] == "2025-12-31"]
    write_csv(project / "same-day-group.csv", group)
    write_csv(project / "same-day-expected.csv", [r for r in expected if r["date"] == "2025-12-31"])
    saved("recipient-october.joblib", "recipient-october.json", "same-day-group.csv", "same-day-out.csv", "october-day-group")
    check("same-day-out.csv", "same-day-expected.csv", "2025-10-01", "six shop group on same date")
    write_csv(project / "shuffled.csv", request[::-1])
    saved("recipient-october.joblib", "recipient-october.json", "shuffled.csv", "shuffled-out.csv", "october-shuffled")
    check("shuffled-out.csv", "recipient-october.csv", "2025-10-01", "all rows reversed")

    manifest = json.loads((E / "second-inputs-manifest.json").read_text())
    assert all(digest(SOURCE / n) == v["sha256"] for n,v in manifest["files"].items())
    out.update(snapshot_unchanged=True, first_author_knowledge_needed=None,
               limitations=["Approved calendar at issue is explicitly assumed; source CSV does not establish approval timestamp.",
                            "No new forecast-accuracy or economic-savings claim; October run tests transfer and cutoff only.",
                            "Notebook not repeated: this receipt executes documented CLI; prior clean notebook check remains separately recorded."])
    (E / "verification2.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
