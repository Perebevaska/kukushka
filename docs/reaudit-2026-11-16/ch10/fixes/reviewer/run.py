"""Run unchanged saved programs using one local copy of the input per submission."""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

here = Path(__file__).resolve().parent
chapter = here.parents[1]
root = chapter.parents[2]
phase = sys.argv[1]
surface = 'pyodide' if sys.platform == 'emscripten' else 'native'
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
sys.path.insert(0,str(root/'site/assets'))
import harness

cases=json.loads((here/'before-programs.json').read_text())
if phase=='after':
    cases.extend(json.loads((here/'after-only-programs.json').read_text()))
if phase=='after' and (here/'migrations.json').exists():
    for migration in json.loads((here/'migrations.json').read_text()):
        case=next(p for p in cases if p['id']==migration['id'])
        assert hashlib.sha256(case['code'].encode()).hexdigest()==case['code_sha256']
        case['code']=migration['code']
        case['migration']=migration['why']
task_file = chapter/('technical/chapter-export.json' if phase=='after' else 'check-evidence/before-tasks.json')
records = json.loads(task_file.read_text())
tasks={t['lesson']+'/'+t['id']:t for t in records}
out=[]
for p in cases:
    item=tasks[p['task']]
    old=Path.cwd()
    with tempfile.TemporaryDirectory() as temp:
        try:
            os.chdir(temp)
            for filename in item['files']:
                source=(chapter/'check-evidence/data-baseline'/filename).read_text()
                if p.get('shift_final') and filename=='daily_sales.csv':
                    csvreader=csv.DictReader(io.StringIO(source))
                    sink=io.StringIO()
                    writer=csv.DictWriter(sink,csvreader.fieldnames)
                    writer.writeheader()
                    for row in csvreader:
                        if row['date']>='2025-07-01': row['revenue_k']=str(float(row['revenue_k'])+p['shift_final'])
                        writer.writerow(row)
                    source=sink.getvalue()
                Path(filename).write_text(p.get('fixture',{}).get(filename,source))
            setup=item.get('setup') or ''
            if p.get('ticks'):setup+='\n_review_clock = iter('+repr(p['ticks'])+')\n_measurement_clock = lambda: next(_review_clock)\n'
            result=harness.run(p['code'],item['check'],setup)
            r=dict(id=p['id'],task=p['task'],expected=p['expected'],code_sha256=hashlib.sha256(p['code'].encode()).hexdigest(),error=result['error'],check=result['check'],stdout=result['out'])
            if p.get('oracle'):
                independently=harness.run(p['code'],'import numpy as _np\n'+p['oracle'],setup)
                r['independent_boundary']=independently['check']
            out.append(r)
        finally: os.chdir(old)
    (here/f'{phase}-{surface}.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(r['id'],r['check'],flush=True)
