from pathlib import Path
import nbformat
from nbclient import NotebookClient
D=Path(__file__).resolve().parent
p=D/'own-native-input-correction.ipynb'
nb=nbformat.read(p,as_version=4)
try:
    NotebookClient(nb,timeout=240,kernel_name='python3',resources={'metadata':{'path':str(D)}}).execute()
finally:
    nbformat.write(nb,p)
print('Executed with outputs:',p)
