import json,io,contextlib,os,traceback,sys,base64
from pathlib import Path
D=Path(__file__).parent.resolve();p=Path(sys.argv[1]).resolve();os.chdir(D)
n=json.loads(p.read_text());ns={'__name__':'__main__'};i=0
for c in n['cells']:
 if c['cell_type']!='code':continue
 i+=1;c['execution_count']=i;c['outputs']=[];out=io.StringIO()
 try:
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):exec(compile(''.join(c['source']),str(p)+f':cell{i}','exec'),ns)
 except BaseException as e:
  c['outputs'].append(dict(output_type='error',ename=type(e).__name__,evalue=str(e),traceback=traceback.format_exc().splitlines()));print(out.getvalue());traceback.print_exc();p.write_text(json.dumps(n,ensure_ascii=False,indent=1));raise
 c['outputs'].insert(0,dict(output_type='stream',name='stdout',text=out.getvalue().splitlines(True)));print(out.getvalue())
p.write_text(json.dumps(n,ensure_ascii=False,indent=1))
