from pathlib import Path
import json,io,contextlib,os,traceback,base64
D=Path(__file__).parent.resolve();os.chdir(D);p=D/'project-retest.ipynb';n=json.loads(p.read_text());ns={'__name__':'__main__'};num=0
for c in n['cells']:
 if c['cell_type']!='code':continue
 num+=1;c['execution_count']=num;c['outputs']=[];out=io.StringIO()
 try:
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):exec(compile(''.join(c['source']),f'project-retest:cell{num}','exec'),ns)
 except BaseException as e:
  c['outputs'].append(dict(output_type='error',ename=type(e).__name__,evalue=str(e),traceback=traceback.format_exc().splitlines()));p.write_text(json.dumps(n,ensure_ascii=False,indent=1));raise
 c['outputs'].append(dict(output_type='stream',name='stdout',text=out.getvalue().splitlines(True)));print(out.getvalue())
 if "plt.savefig('own-weekly.png')" in ''.join(c['source']):c['outputs'].append(dict(output_type='display_data',metadata={},data={'image/png':base64.b64encode(Path('own-weekly.png').read_bytes()).decode()}))
p.write_text(json.dumps(n,ensure_ascii=False,indent=1))
print('EXECUTED',num,'code cells in fresh Python namespace, not nbclient')
