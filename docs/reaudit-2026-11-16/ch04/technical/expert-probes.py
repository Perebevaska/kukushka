"""Expected outcomes recorded before running. Run with a build.py --export file as argument."""
from contextlib import chdir
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import sys

from transfer_data import make_extract

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "site/assets"))
import harness

tasks = {(t["lesson"].split("/")[-1], t["id"]): t for t in json.loads(Path(sys.argv[1]).read_text()) if t["kind"] == "task" and t["lesson"].startswith("ch04/")}


def run(key, case, expected, *, after="", change=None, branch=False):
    t = tasks[key]
    source = t["solution"]
    if change:
        old, new = change
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    code = source + "\n" + after
    with TemporaryDirectory() as tmp, chdir(tmp):
        for f in t["files"]:
            shutil.copyfile(ROOT / "site/data" / f, f)
        if branch:
            make_extract(Path("deliveries.csv"))
        result = harness.run(code, t["check"], t["setup"], False)
    passed = result["ok"] and result["check"]["passed"]
    print(json.dumps({"id":"/".join(key), "case":case,"expected":expected,"actual":passed,
                      "feedback":result.get("check") or result.get("error")},ensure_ascii=False))
    assert passed == expected


key = ("07c-metrics", "funnel-platform")
run(key,"author",True)
run(key,"reorder four complete groups",True,after="pay_conv = pay_conv.iloc[::-1]")
run(key,"swap platform names only",False,after='pay_conv.index = pd.MultiIndex.from_tuples([({"ios":"android","android":"ios"}[p], m) for p,m in pay_conv.index])')
key = ("09-project","walkers")
run(key,"author",True)
run(key,"complete row and column permutation",True,after="pv = pv.iloc[::-1, ::-1]")
run(key,"exchange only courier labels",False,after="pv.columns = pv.columns[::-1]")
run(key,"changed branch and data-driven leader",True,branch=True)
run(key,"changed branch but fixed original leader",False,branch=True,
    change=('group = ok.groupby("courier", sort=True)["late"].mean().idxmax()', 'group = "пеший"'))
key = ("06-correlation","spearman")
run(key,"author full-precision difference",True)
run(key,"equivalent SciPy through pandas",True,after='diff = round(d.distance_km.corr(d.actual_min, method="spearman") - d.distance_km.corr(d.actual_min), 2)')
run(key,"old second hint",False,after='diff = round(r_spearman - r_pearson, 2)')
