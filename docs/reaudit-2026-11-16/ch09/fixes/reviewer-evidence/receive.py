"""Read a frozen student receipt in a clean directory and independently verify it.

Usage: python receive.py ARCHIVE OUT [--run-notebook]. COURSE_DATA is the same
documented baseline on both receipts. Archive names belong to this local audit.
"""
import argparse
import hashlib
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

here = Path(__file__).resolve().parent
baseline = here.parents[1] / 'technical' / 'data-baseline'
p = argparse.ArgumentParser()
p.add_argument('archive', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--run-notebook', action='store_true')
a = p.parse_args()
archive, output = a.archive.resolve(), a.output.resolve()
report = {'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
with tempfile.TemporaryDirectory() as td:
    work = Path(td)
    with tarfile.open(archive) as t:
        t.extractall(work, members=[m for m in t.getmembers() if not Path(m.name).name.startswith('._')], filter='data')
    os.environ['COURSE_DATA'] = str(baseline)
    os.chdir(work)
    sys.path.insert(0, str(work))
    nbpath = work / 'project.ipynb'
    cells = json.loads(nbpath.read_text())['cells']
    report['code_cells'] = sum(c['cell_type']=='code' for c in cells)
    if a.run_notebook:
        from nbclient import NotebookClient
        import nbformat
        nb = nbformat.read(nbpath, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == 'code':
                cell.outputs = []
                cell.execution_count = None
        NotebookClient(nb, timeout=120, kernel_name='python3').execute(cwd=str(work))
        report['clean_execution'] = [c.execution_count for c in nb.cells if c.cell_type=='code']
    inner = work / 'artifacts/internal'
    public = work / 'artifacts/contractor-demo'
    names = ['gender','age','income_k','family_size']
    source = pd.read_csv(baseline/'family_members.csv').set_index('member_id')
    train_ids = pd.read_csv(inner/'train-ids.csv').member_id
    scored = pd.read_csv(inner/'test-predictions.csv').set_index('member_id')
    assert source.index.is_unique and scored.index.is_unique and train_ids.is_unique and set(train_ids).isdisjoint(scored.index)
    assert set(train_ids) | set(scored.index) == set(source.index)
    tr, te = source.loc[train_ids], source.loc[scored.index]
    X, test = tr[names].to_numpy(), te[names].to_numpy()
    y, target = tr.spend_k.to_numpy(), te.spend_k.to_numpy()
    P = np.load(inner/'key.npy')
    features = ['f1','f2','f3','f4']
    expected_files = ['new-hidden.csv','test-hidden.csv','train-hidden.csv']
    assert sorted(x.name for x in public.iterdir()) == expected_files
    A = pd.read_csv(public/'train-hidden.csv')
    B = pd.read_csv(public/'test-hidden.csv')
    N = pd.read_csv(public/'new-hidden.csv')
    assert list(A)==features+['spend_k'] and list(B)==list(N)==features
    assert np.allclose(A[features],X@P) and np.allclose(B,test@P)
    assert np.allclose(A.spend_k,y) and np.allclose(scored.actual_spend_k,target)
    raw = LinearRegression().fit(X,y)
    external = LinearRegression().fit(A[features],A.spend_k)
    submitted = joblib.load(inner/'hidden-model.joblib')
    actual = submitted.predict(test@P)
    assert np.allclose(scored.open_pred_k,raw.predict(test)) and np.allclose(scored.hidden_pred_k,actual)
    assert np.allclose(external.predict(B),actual)
    new = pd.read_csv(inner/'new-member.csv')[names].to_numpy()
    assert np.allclose(N,new@P)
    report['receipt'] = dict(train=len(X),test=len(test),public_files=expected_files,
        actual_r2=r2_score(target,actual),raw_r2=r2_score(target,raw.predict(test)),
        actual_mae=mean_absolute_error(target,actual),max_model_delta=float(np.max(np.abs(raw.predict(test)-actual))),
        max_table_delta=float(np.max(np.abs(actual-scored.hidden_pred_k))),
        new_raw=float(raw.predict(new)[0]),new_hidden=float(submitted.predict(new@P)[0]),
        new_public=float(external.predict(N)[0]))
    # Recipient independently trains again; this evaluates the math only.
    fresh = np.array([[0,48,137,2]], dtype=float)
    P2 = np.random.default_rng(317).normal(size=(4,4))
    rotated = LinearRegression().fit(X@P2,y)
    report['independent_rekey'] = dict(new_row=fresh.tolist(),condition=float(np.linalg.cond(P2)),
        fixed_model_old_key=float(submitted.predict(fresh@P)[0]),same_model_wrong_key=float(submitted.predict(fresh@P2)[0]),
        rekeyed=float(rotated.predict(fresh@P2)[0]),open=float(raw.predict(fresh)[0]))
    assert np.allclose(rotated.predict(fresh@P2),raw.predict(fresh)) and not np.allclose(submitted.predict(fresh@P2),raw.predict(fresh))
    # Without the full key, a rank-one known subset still discloses some values.
    known = X[:4]
    assert np.linalg.matrix_rank(known)==4
    recovered = np.linalg.solve(known,A[features].to_numpy()[:4])
    report['recovery_max_error'] = float(np.abs(np.linalg.solve(recovered.T,B.to_numpy().T).T-test).max())
    report['readme_tmp_paths'] = [s for s in (work/'README.md').read_text().splitlines() if '/private/tmp/' in s]
output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
