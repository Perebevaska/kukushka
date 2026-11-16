from pathlib import Path
import nbformat
from nbclient import NotebookClient
D=Path(__file__).resolve().parent
p=D/'project-template.ipynb'
nb=nbformat.read(p,as_version=4)
client=NotebookClient(nb,timeout=240,kernel_name='python3',resources={'metadata':{'path':str(D)}})
try:
 client.execute()
finally:
 nbformat.write(nb,p)
print('Executed and saved outputs',p)
