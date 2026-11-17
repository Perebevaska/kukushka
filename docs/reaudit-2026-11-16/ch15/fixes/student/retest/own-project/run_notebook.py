"""Execute the full revised report using an existing Python environment kernel."""
from pathlib import Path
import argparse
import nbformat
from nbclient import NotebookClient
p=argparse.ArgumentParser();p.add_argument('--kernel',default='python3');a=p.parse_args()
path=Path('final_project.ipynb');book=nbformat.read(path,as_version=4)
NotebookClient(book,timeout=1800,kernel_name=a.kernel,resources={'metadata':{'path':str(Path.cwd())}}).execute()
nbformat.write(book,path)
errors=[o for cell in book.cells if cell.cell_type=='code' for o in cell.outputs if o.output_type=='error']
assert not errors
assert Path('reports/revision/industry-ablation.json').is_file()
print('CLEAN RESTART AND RUN ALL',len(book.cells),'cells',sum(c.cell_type=='code' for c in book.cells),'code cells; no errors; industry artifact recreated')
