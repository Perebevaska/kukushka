from pathlib import Path
import json,nbformat,hashlib,os
from nbclient import NotebookClient
root=Path('/private/tmp/kuch02round/student-retest')
w=root/'work'
empty=w/'data';empty.mkdir(exist_ok=True)
assert not list(empty.iterdir()), 'work/data должна быть пуста'
first=''.join(json.loads((root/'ch02-project-template.ipynb').read_text())['cells'][1]['source'])
sets={'autumn':['orders_3m.csv','shops.csv','menu.csv'],'zerno-sql':['zdb_shops.csv','zdb_menu.csv','zdb_guests.csv','zdb_promos.csv','zdb_orders.csv','zdb_items.csv']}
report=[]
for name,files in sets.items():
 p=w/(name+'.ipynb');nb=nbformat.read(p,as_version=4)
 initial=next(c for c in nb.cells if c.cell_type=='code')
 initial.source=first
 selected=False
 for c in nb.cells:
  if c.cell_type!='code' or c is initial:continue
  if not selected and ('DATA /' in c.source or 'DATA/' in c.source):
   c.source='DATA = data_folder('+', '.join(repr(f) for f in files)+')\n'+c.source
   selected=True
  c.outputs=[];c.execution_count=None
 assert selected
 initial.outputs=[];initial.execution_count=None
 nbformat.write(nb,p)
 NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(w)}}).execute()
 nbformat.write(nb,p)
 paths=[o.text.strip() for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='stream' and 'Папка данных:' in o.text]
 print(name,paths)
 assert paths and str(root/'data') in paths[0]
 dest=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch02/fixes/student')/(name+'.ipynb')
 dest.write_bytes(p.read_bytes())
 sha=hashlib.sha256(dest.read_bytes()).hexdigest()
 report.append({'name':name,'sha256':sha,'selected_path_output':paths,'empty_local_data':not list(empty.iterdir())})
namespace={};exec(first,namespace)
incomplete=w/'incomplete-run';incomplete.mkdir(exist_ok=True)
(incomplete/'data').mkdir(exist_ok=True)
prior=Path.cwd();os.chdir(incomplete)
for name,files in sets.items():
 try:namespace['data_folder'](*files)
 except FileNotFoundError as e:
  report.append({'name':name,'incomplete_error':type(e).__name__+': '+str(e)})
os.chdir(prior)
log=w/'data-folder-verification.json';log.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(log.read_text())
