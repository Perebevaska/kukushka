"""Execute the delivered notebook in a fresh directory and independently audit its outputs."""
import hashlib
import json
import math
import shutil
import statistics
import tempfile
from base64 import b64decode
from pathlib import Path

import nbformat
import pandas as pd
from nbclient import NotebookClient
from PIL import Image

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent / "student"
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checklist(nb):
    codes = [c for c in nb.cells if c.cell_type == 'code']
    assert [c.execution_count for c in codes] == list(range(1, len(codes)+1))
    all_outputs = [o for c in codes for o in c.outputs]
    assert not any(o.output_type == 'error' for o in all_outputs)
    pngs = [o.data['image/png'] for o in all_outputs if 'image/png' in o.get('data', {})]
    assert len(pngs) == 1
    texts = [o.get('text', o.get('data', {}).get('text/markdown', o.get('data', {}).get('text/plain',''))) for o in all_outputs if 'image/png' not in o.get('data', {})]
    return texts, hashlib.sha256(b64decode(pngs[0])).hexdigest()

with tempfile.TemporaryDirectory(prefix="recipient-ch05-") as temp:
    directory = Path(temp)
    for name in ('promise.ipynb', 'ab_promise.csv'):
        shutil.copyfile(BOOK/name,directory/name)
    assert digest(directory/'ab_promise.csv') == digest(HERE.parents[3]/'site/data/ab_promise.csv')
    saved = nbformat.read(directory/'promise.ipynb', as_version=4)
    nb = nbformat.reads(nbformat.writes(saved), as_version=4)
    for c in nb.cells:
        if c.cell_type == 'code':
            c.outputs = []
            c.execution_count = None
    NotebookClient(nb, kernel_name='python3', timeout=160).execute(cwd=temp)
    oldtext, oldimg = checklist(saved)
    newtext, newimg = checklist(nb)
    assert oldtext == newtext and oldimg == newimg
    png = directory/"promise-chart.png"
    assert digest(png)==digest(BOOK/png.name)
    ab=pd.read_csv(directory/'ab_promise.csv')
    assert ab.session_id.is_unique and len(ab)==7895
    assert ab.loc[ab.ordered.eq(0),'amount'].eq(0).all()
    groups=[x for _, x in ab.groupby("group",sort=True)]
    arpu = [statistics.mean(g.amount) for g in groups]
    d = arpu[1]-arpu[0]
    se = math.sqrt(sum(statistics.variance(g.amount)/len(g) for g in groups))
    lower, upper=d-1.96*se,d+1.96*se
    purchases=[g[g.ordered.eq(1)] for g in groups]
    rates=[g.late.sum()/len(g) for g in purchases]
    effect=(rates[1]-rates[0])*100
    late_se=100*math.sqrt(sum(p*(1-p)/len(g) for p,g in zip(rates,purchases)))
    assert lower < -10 < upper
    brief=next(t for t in newtext if 'Три предложения руководителю' in t)
    assert 'неопределённо' in brief and f'{lower:.1f}…{upper:.1f}' in brief and f'{effect:.1f}' in brief
    artifacts={}
    for filename in ('boundary-decisions.json','promise-full-decisions.json'):
        assert digest(directory/filename)==digest(BOOK/filename)
        artifacts[filename]=digest(directory/filename)
    controls=json.loads((directory/'boundary-decisions.json').read_text())
    assert controls['X']['нижняя_для_отчёта'] == controls['Y']['нижняя_для_отчёта'] == '-10.0'
    for key,expected_lower,expect in [('X',-9.96,'внедрять'),('Y',-10.04,'неопределённо')]:
        assert controls[key]['rev_lo_full']==expected_lower and controls[key]['решение']==expect
    outputs=json.loads((directory/'promise-full-decisions.json').read_text())
    subsets={'вся выгрузка':ab,**dict(list(ab.groupby('city')))}
    assert set(outputs)==set(subsets)
    for name,frame in subsets.items():
        a,b=[g for _,g in frame.groupby('group')]
        revdiff=statistics.mean(b.amount)-statistics.mean(a.amount)
        revse=math.sqrt(statistics.variance(a.amount)/len(a)+statistics.variance(b.amount)/len(b))
        lo,hi=revdiff-1.96*revse,revdiff+1.96*revse
        oa,ob=a[a.ordered.eq(1)],b[b.ordered.eq(1)]
        pavg=(oa.late.sum()+ob.late.sum())/(len(oa)+len(ob))
        diff=ob.late.mean()-oa.late.mean()
        z=diff/math.sqrt(pavg*(1-pavg)*(1/len(oa)+1/len(ob)))
        late_p=math.erfc(abs(z)/math.sqrt(2))
        srm_p=math.erfc(abs(len(a)-len(b))/math.sqrt(2*len(frame)))
        expected='не внедрять' if srm_p<.01 or diff>=0 or late_p>=.05 or hi< -10 else 'внедрять' if lo> -10 else 'неопределённо'
        assert abs(outputs[name]['rev_lo_full']-lo)<1e-8 and abs(outputs[name]['rev_hi_full']-hi)<1e-8 and outputs[name]['decision']==expected
    cells=sum(c.cell_type=='code' for c in nb.cells)
    assert cells==10
    summary=dict(derived_artifacts=artifacts,independently_verified_reports=list(subsets),inputs=['promise.ipynb','ab_promise.csv'],code_cells=cells,text_outputs=len(newtext),identical_outputs=True,
        inline_image_sha256=newimg,chart_sha256=digest(png),chart_pixels=Image.open(png).size,
        csv_sha256=digest(directory/'ab_promise.csv'),notebook_sha256=digest(BOOK/'promise.ipynb'),
        session_counts=[len(g) for g in groups],order_counts=[len(g) for g in purchases],late_counts=[int(g.late.sum()) for g in purchases],
        late_diff_pp=effect,late_interval_pp=[effect-1.96*late_se,effect+1.96*late_se],revenue_diff=d,revenue_interval=[lower,upper],decision='неопределённо')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
