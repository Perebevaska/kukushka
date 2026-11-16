import json,os,sys,shutil,tempfile,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
import matplotlib.pyplot as plt  # Prewarm cache outside captured learner output; environment diagnosis only.
sys.path.insert(0,str(B));import frozen_harness as harness
row=list(map(json.loads,(B/'programs.jsonl').read_text().splitlines()))[3]
t=next(t for t in json.loads((B/'tasks.json').read_text()) if (t['lesson'],t['id'])==(row['lesson'],row['task']))
with tempfile.TemporaryDirectory() as folder:
 for f in t['files']:shutil.copy2(B/'data'/f,Path(folder)/f)
 os.chdir(folder);result=harness.run(row['code'],t['check'],t['setup'],bool(t.get('display')))
record=dict(row,index=3,runtime='CPython environment replay',MPLCONFIGDIR=os.environ.get('MPLCONFIGDIR'),programs_sha256=hashlib.sha256((B/'programs.jsonl').read_bytes()).hexdigest(),raw=result,passed=result.get('check',{}).get('passed'))
(B/'environment-native-replay.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));print(record['passed'])
