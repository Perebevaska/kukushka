from pathlib import Path
import nbformat
from nbclient import NotebookClient
root=Path(__file__).parent.resolve()
for name in ['sites-project.ipynb','final-project.ipynb']:
    p=root/name
    notebook=nbformat.read(p,as_version=4)
    nbformat.validate(notebook)
    print('Executing',name,flush=True)
    client=NotebookClient(notebook,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(root)}})
    try:
        client.execute()
    finally:
        nbformat.write(notebook,p)
    errors=[(i,o.get('ename'),o.get('evalue')) for i,c in enumerate(notebook.cells) for o in c.get('outputs',[]) if o.get('output_type')=='error']
    assert not errors,errors
    counts=[c.execution_count for c in notebook.cells if c.cell_type=='code']
    assert counts==list(range(1,len(counts)+1)),counts
    print('Clean kernel PASS',name,'code cells',len(counts),flush=True)
