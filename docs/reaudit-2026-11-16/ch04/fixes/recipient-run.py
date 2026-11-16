"""Replay the submitted notebooks in isolated fresh kernels, saving recipient evidence only."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from PIL import Image, ImageDraw
import nbformat
from nbclient import NotebookClient

base = Path(__file__).resolve().parent
student = base/'student'
def digest(raw):
    return sha256(raw).hexdigest()

def render_text(nb):
    return [[(o.get('text') or o.get('data', {}).get('text/markdown') or o.get('data', {}).get('text/plain')) for o in c.get('outputs',[])] for c in nb.cells]

result={}
with TemporaryDirectory() as tmp:
    scratch=Path(tmp)
    for source in sorted(student.glob('*.ipynb')):
        folder=scratch/source.stem
        folder.mkdir()
        shutil.copytree(student/'data', folder/'data')
        nb=nbformat.read(source,as_version=4)
        before=render_text(nb)
        # The remote file name embedded in Markdown should not change when the notebook is copied.
        for cell in nb.cells:
            if cell.cell_type=='code':
                cell.outputs=[]
                cell.execution_count=None
        NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(folder)}}).execute()
        after=render_text(nb)
        diffs=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        image_checks=[]
        for f in sorted(folder.glob('figures-*/*.png')):
            ref=student/f.relative_to(folder)
            with Image.open(f) as a,Image.open(ref) as b:
                image_checks.append({'file':str(f.relative_to(folder)), 'sha256':digest(f.read_bytes()),
                                     'identical_file':f.read_bytes()==ref.read_bytes(),
                                     'identical_pixels':a.size==b.size and a.convert('RGB').tobytes()==b.convert('RGB').tobytes()})
        significant=[{'cell':i,'saved':before[i],'fresh':after[i]} for i in diffs if i!=1]
        result[source.name]={'sha256':digest(source.read_bytes()),'executed_cells':sum(c.cell_type=='code' for c in nb.cells),
                             'image_checks':image_checks, 'different_output_cells':diffs, 'differences_except_environment':significant,
                             'first_summary':after[3], 'two_findings':after[27], 'final_summary':after[-1]}
    panels=[]
    for name in ('scale','promise','weeks','ratings','own'):
        pair=[]
        for fn in ('delivery_delays','delivery_branch'):
            file=next((scratch/fn).glob('figures-*/'+name+'.png'))
            im=Image.open(file).convert('RGB')
            im.thumbnail((540,350))
            pair.append(im.copy())
        panels.append(pair)
    display=Image.new('RGB',(1080,sum(max(a.height,b.height) for a,b in panels)), 'white')
    y=0
    for a,b in panels:
        display.paste(a,(0,y));display.paste(b,(540,y));y+=max(a.height,b.height)
    display.save('/private/tmp/ch04-recipient-figures.png')
print(json.dumps(result,ensure_ascii=False,indent=2))
