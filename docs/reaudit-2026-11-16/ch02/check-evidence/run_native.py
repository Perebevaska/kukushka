"""Native counterpart to run_probes.mjs; build/export only, never generate site."""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
D=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'site/assets')]
import build
import harness
import pandas as pd
print(sys.version, 'pandas',pd.__version__)
build.CH_DISPLAY['ch02']=True
lessons={('ch02',p.stem):build.parse_lesson(p) for p in (ROOT/'content/ch02').glob('*.md') if p.stem not in ('intro','test')}
build.export(lessons,D/'tasks-after.json')
REVIEW_BEFORE='--review-before' in sys.argv
PROMO_BEFORE='--promo-before' in sys.argv
ROUNDING_BEFORE='--promo-rounding-before' in sys.argv
T={(x['lesson'].split('/')[-1],x['id']):x for x in json.loads((D/('tasks-before-promo-rounding-fix.json' if ROUNDING_BEFORE else 'tasks-before-promo-fix.json' if PROMO_BEFORE else 'tasks-before-review-fixes.json' if REVIEW_BEFORE else 'tasks-after.json')).read_text()) if x['kind']=='task'}
all_results=[]
for after in ((True,) if REVIEW_BEFORE or PROMO_BEFORE or ROUNDING_BEFORE else (False,True)):
    cases=json.loads((D/'probes-before.json').read_text())
    if after:
        for case in cases:
            t=T[case['lesson'],case['task']];case['check']=t['check'];case['setup']=t.get('setup')
        for lesson,task in sorted({(x['lesson'],x['task']) for x in cases}):
            t=T[lesson,task];cases.append(dict(lesson=lesson,task=task,case='current-author-solution',expected=True,code=t['solution'],check=t['check'],setup=t.get('setup'),files=t['files']))
    results=[]
    for x in cases:
        previous=Path.cwd()
        with tempfile.TemporaryDirectory(prefix='ch02-native-') as folder:
            try:
                os.chdir(folder)
                for file in x['files']:
                    shutil.copy(ROOT/'site/data'/file,file)
                if x.get('prepare'):
                    exec(x['prepare'],{})
                r=harness.run(x['code'],x['check'],x.get('setup'),False)
            finally:
                os.chdir(previous)
        actual=bool(r.get('check',{}).get('passed'))
        match=actual==x['expected']
        results.append(dict(x,result=r,actual=actual,match=match))
        print(('after' if after else 'before'),('OK' if match else 'DEFECT'),x['lesson']+'/'+x['task'],x['case'],'expected',x['expected'],'actual',actual,r.get('check',{}).get('msg',''))
    (D/('native-results-before-promo-rounding-fix.json' if ROUNDING_BEFORE else 'native-results-before-promo-fix.json' if PROMO_BEFORE else 'native-results-before-review-fixes.json' if REVIEW_BEFORE else 'native-results-after.json' if after else 'native-results-before.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2))
    all_results.append(results)
if not REVIEW_BEFORE and not PROMO_BEFORE and not ROUNDING_BEFORE:
    assert all(x['match'] for x in all_results[-1]), 'New checker regressions failed'
print('Native final:',sum(x['match'] for x in all_results[-1]),'of',len(all_results[-1]),'as expected')
