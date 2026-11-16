"""Usage: python native.py before|after PATH_TO_REAL_EXPORT"""
import json
import os
from pathlib import Path
import sys
import tempfile
import shutil
from threadpoolctl import threadpool_limits

here = Path(__file__).resolve().parent
chapter = here.parents[1]
root = here.parents[4]
sys.path.insert(0, str(root/'site/assets'))
import harness

phase, export, *rest = sys.argv[1:]
program_path = rest[0] if rest else "programs.jsonl"
tasks = {(t['lesson'], t['id']): t for t in json.loads(Path(export).read_text()) if t['kind']=='task'}
rows = [json.loads(line) for line in (here/program_path).read_text().splitlines()]
with threadpool_limits(1), (here/f'{phase}-native.jsonl').open('w') as out:
    for row in rows:
        t = tasks[row['lesson'], row['task']]
        with tempfile.TemporaryDirectory() as folder:
            original = Path.cwd()
            try:
                os.chdir(folder)
                for f in t['files']:
                    shutil.copy(chapter/'technical/data-baseline'/f, f)
                r = harness.run(row['code'], row.get('review_check') or t['check'], t.get('setup') or '', False)
                result = dict(id=row['id'], ok=r['ok'], passed=r['check']['passed'], msg=r['check']['msg'], error=r['error'], stdout=r['out'])
                out.write(json.dumps(result, ensure_ascii=False)+'\n')
                out.flush()
            finally:
                os.chdir(original)
