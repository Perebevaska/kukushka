from pathlib import Path
import nbformat
from nbclient import NotebookClient
p=Path('/private/tmp/kuch02round/student-retest/work/zerno-sql.ipynb')
nb=nbformat.read(p,as_version=4)
changes=0
for c in nb.cells:
 if c.cell_type!='code':continue
 lines=c.source.splitlines()
 for i,line in enumerate(lines):
  if line.startswith('promo_items["Акция"]='):
   expr=line.split('=',1)[1]
   lines[i]='promo_report=promo_items.assign(**{"Акция": '+expr+'})'
   changes+=1
 c.source='\n'.join(lines).replace('display(promo_items,margin)','display(promo_report,margin)')
 c.outputs=[];c.execution_count=None
assert changes==1
nbformat.write(nb,p)
NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(p.parent)}}).execute()
nbformat.write(nb,p)
print('Fixed display copy, executed',len(nb.cells),'cells')
