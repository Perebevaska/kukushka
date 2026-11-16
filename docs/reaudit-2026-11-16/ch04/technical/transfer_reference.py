"""Recompute the delivery comparison from raw rows using the standard library."""
import csv
import json
from math import ceil
from pathlib import Path
from tempfile import TemporaryDirectory
from transfer_data import make_extract

ROOT = Path(__file__).resolve().parents[4]


def profile(path):
    with path.open(newline='') as file:
        rows = list(csv.DictReader(file))
    valid = [r for r in rows if r['actual_min'] and 1 <= float(r['actual_min']) <= 299]
    groups = {}
    for label in sorted({r['courier'] for r in valid}):
        trips = [r for r in valid if r['courier']==label]
        groups[label] = {'late':sum(float(r['actual_min']) > int(r['promised_min']) for r in trips),
                         'n':len(trips)}
    leader = max(groups,key=lambda label: groups[label]['late']/groups[label]['n'])
    scenarios = {}
    for old_promise in (30, 45):
        minutes = sorted(float(r['actual_min']) for r in valid
                         if r['courier']==leader and int(r['promised_min'])==old_promise)
        index = (len(minutes)-1)*.8
        low, high = int(index), ceil(index)
        p80 = minutes[low]+(index-low)*(minutes[high]-minutes[low])
        promise = ceil(p80/5)*5
        scenarios[old_promise] = {'trips':len(minutes),'late':sum(x>old_promise for x in minutes),
                                  'p80':round(p80,3),'new_promise':promise,
                                  'within_new_promise':sum(x<=promise for x in minutes)}
    return dict(raw=len(rows),valid=len(valid),late=sum(x['late'] for x in groups.values()),
                group_counts=groups,leader=leader,scenarios=scenarios)


if __name__ == '__main__':
    with TemporaryDirectory() as folder:
        branch=Path(folder)/'branch.csv'
        make_extract(branch)
        print(json.dumps({'original':profile(ROOT/'site/data/deliveries.csv'),'branch':profile(branch)},ensure_ascii=False,indent=2))
