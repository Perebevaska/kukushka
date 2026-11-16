import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
p=Path(sys.argv[1]).resolve();n=nbformat.read(p,as_version=4)
NotebookClient(n,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(p.parent)}}).execute()
nbformat.write(n,p)
print('Saved executed notebook',p)
