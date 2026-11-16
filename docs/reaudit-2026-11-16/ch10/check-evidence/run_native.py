"""Run saved technical submissions, with immutable expected verdicts and separate transfer oracles."""
import argparse,json,os,shutil,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'site/assets'))
import harness
from threadpoolctl import threadpool_limits
threadpool_limits(limits=1)
p=argparse.ArgumentParser(); p.add_argument('phase',choices=['before','after']); p.add_argument('--bundle'); a=p.parse_args(); bundle=a.bundle or a.phase
tasks={t['lesson']+'/'+t['id']:t for t in json.loads((HERE/f'{a.phase}-tasks.json').read_text())}
programs=HERE/((bundle+'-programs.jsonl') if a.bundle else ('after-programs.jsonl' if a.phase=='after' else 'programs.jsonl'))
rows=[json.loads(s) for s in programs.read_text().splitlines()]
data=HERE/'data-baseline'
assert data.is_dir(),data
out=HERE/f'{bundle}-native.jsonl'
results=[]
for row in rows:
    item=tasks[row['lesson']+'/'+row['task']]
    old=Path.cwd()
    with tempfile.TemporaryDirectory() as folder:
        try:
            os.chdir(folder)
            for name in item['files']: shutil.copy(data/name,name)
            setup=item.get('setup') or ''
            if row.get('clock_ticks'):
                setup+='\n_fixture_ticks=iter('+repr(row['clock_ticks'])+')\n_measurement_clock=lambda:next(_fixture_ticks)\n'
            r=harness.run(row['code'],item['check'],setup,False)
            result=dict(row,ok=r['ok'],passed=r['check']['passed'],message=r['check']['msg'],error=r['error'],stdout=r['out'])
            if row.get('oracle'):
                for name in item['files']: shutil.copy(data/name,name)
                o=harness.run(row['code'],item['check']+'\n'+row['oracle'],item.get('setup'),False)
                result['transfer_oracle']={k:o[k] for k in ['ok','check','error']}
            results.append(result)
        finally: os.chdir(old)
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
    print(json.dumps({k:result[k] for k in ['id','lesson','task','expected','ok','passed','message']},ensure_ascii=False),flush=True)
import numpy,pandas,scipy,sklearn
(HERE/f'{bundle}-native-environment.json').write_text(json.dumps(dict(python=sys.version,numpy=numpy.__version__,pandas=pandas.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),indent=2))
print('Completed',len(results),'programs; normative matches',sum((r['ok'] or r.get('expected_error',False)) and r['passed']==r['expected'] for r in results))
