"""Submit programs to the actual notebook magic's public Python entry point."""
import contextlib,io,json,sys,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parents[4]
sys.path.insert(0,str(root/'site/notebooks'))
import dsc
site=Path(sys.argv[1]).resolve()
phase=sys.argv[2]
dsc.DATA=here.parents[1]/'technical/data-baseline'
dsc.TASKS_DIR=site/'notebooks/tasks'
with tempfile.TemporaryDirectory() as td, (here/(phase+'-catalog.jsonl')).open('w') as stream:
    dsc.WORK=Path(td)
    for r in json.loads((here/(phase+'-cases.json')).read_text()):
        with contextlib.redirect_stdout(io.StringIO()):
            result=dsc.run_task(r['key'],r['code'],{'__name__':'__main__'})
        print(json.dumps(dict(id=r['id'],expected=r['expected'],**result),ensure_ascii=False),file=stream,flush=True)
        print(r['id'],result['passed'],flush=True)
