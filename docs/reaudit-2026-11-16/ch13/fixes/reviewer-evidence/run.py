"""Run one frozen suite on a supplied export, harness and data directory."""
import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path

out = Path(__file__).resolve().parent
phase, export_file, harness_file, data_dir, case_file = sys.argv[1:]
sha = lambda file: hashlib.sha256(Path(file).read_bytes()).hexdigest()
suite = json.loads(Path(case_file).read_bytes())
tasks = {t['id']:t for t in json.loads(Path(export_file).read_bytes()) if t['lesson'].startswith('ch13/') and t['kind']=='task'}
namespace = {}
exec(compile(Path(harness_file).read_text(), harness_file, 'exec'), namespace)
meta = dict(python=sys.version, packages={p:importlib.metadata.version(p) for p in ['pandas','numpy','scikit-learn','matplotlib','scipy']}, harness=sha(harness_file), cases=sha(case_file), export=sha(export_file))
(out / (phase+'-native-meta.json')).write_text(json.dumps(meta, indent=2)+'\n')
os.chdir(data_dir)
with (out / (phase+'-native.jsonl')).open('w') as f:
    for case in suite:
        t = tasks[case['task']]
        r = namespace['run'](case['code'], t['check'], t['setup'], bool(t['display']))
        e = {**{k:case[k] for k in ('id','task','expected')},'ok':r['ok'],'check':r['check'],'error':r['error'],'out':r['out'],'figures':len(r['figs'])}
        print(json.dumps(e,ensure_ascii=False),file=f,flush=True)
        print(case['id'],r['check']['passed'],flush=True)
