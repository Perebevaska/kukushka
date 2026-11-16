"""Read each plot's artists at display time and compare against the independent CSV counts."""
from contextlib import chdir, redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base=Path(__file__).resolve().parent
numbers=json.loads((base/'recipient-numbers.json').read_text())
def eq(actual,expected):
    assert len(actual)==len(expected) and all(math.isclose(float(a),float(b),abs_tol=1e-8) for a,b in zip(actual,expected)),(actual,expected)
def percent(pair):
    return 100*pair[0]/pair[1] if pair[1] else 0
def inspect(name, a, ref):
    heights=[p.get_height() for p in a.patches]
    if name=='scale':
        eq(heights,ref['histogram'])
        eq([p.get_x() for p in a.patches],range(-40,40,5))
        eq(a.lines[0].get_xdata(),[0,0])
    if name=='promise':
        for c in a.containers:
            eq([p.get_height() for p in c], [percent(ref['promises'][c.get_label()][v]) for v in ('30','45','60')])
        assert [t.get_text() for t in a.texts]==[f'n={pair[1]}' if pair[1] else '' for v in ref['promises'].values() for pair in v.values()]
    if name=='weeks':
        for l in a.lines:
            col={'опоздания':0,'снег':1}[l.get_label()]
            eq(l.get_ydata(), [100*v[col]/v[2] for v in ref['weeks'].values()])
            assert [str(x.end_time.date()) if hasattr(x,'end_time') else str(x.date()) for x in l.get_xdata()]==list(ref['weeks'])
    if name=='ratings':
        eq(heights,[p[1] for p in ref['rating_bins']])
        assert [t.get_text() for t in a.texts]==[f'n={p[0]}' for p in ref['rating_bins']]
    if name=='own':
        measures=list(ref['findings'].values())
        for i,c in enumerate(a.containers):
            eq([p.get_height() for p in c],[round(percent(v['all'][i]),1) for v in measures])
        assert [t.get_text() for t in a.texts]==[f'n={v["all"][i][1]}' for i in range(2) for v in measures]
    return {'plot':name,'title':a.get_title(),'x':a.get_xlabel(),'y':a.get_ylabel(),'bars':len(a.patches),'line_points':[len(l.get_xdata()) for l in a.lines]}
result={}
for notebook in sorted((base/'student').glob('*.ipynb')):
    file='deliveries_branch.csv' if notebook.stem=='delivery_branch' else 'deliveries.csv'
    rows=[]
    seq=iter(('scale','promise','weeks','ratings','own'))
    def at_show():
        a=plt.gca()
        rows.append(inspect(next(seq),a,numbers[file]))
        plt.close(a.figure)
    plt.show=at_show
    with TemporaryDirectory() as tmp,chdir(tmp),redirect_stdout(StringIO()):
        shutil.copytree(base/'student/data',Path('data'))
        state={}
        for c in json.loads(notebook.read_text())['cells']:
            if c['cell_type']=='code':
                exec(compile(''.join(c['source']),notebook.name,'exec'),state)
    assert len(rows)==5
    result[notebook.name]=rows
print(json.dumps(result,ensure_ascii=False,indent=2))
