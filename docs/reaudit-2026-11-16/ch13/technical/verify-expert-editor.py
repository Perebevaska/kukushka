"""Check published source using the same chapter parser as the site and offline evidence."""
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser

here=Path(__file__).resolve().parent
root=here.parents[3]
sys.path.insert(0,str(root/'tools'))
import build
def digest(x): return hashlib.sha256(x).hexdigest()
def original(p):
    return subprocess.check_output(['git','show',f'563d774b125387aca7b004c086603e02900a18b1:{p.relative_to(root).as_posix()}'],cwd=root)
result={}
class Disclosure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth=0; self.sample_depth=None; self.prompt_depth=None; self.brief_depth=None
    def handle_starttag(self,tag,attrs):
        if tag=='details': self.depth+=1
    def handle_endtag(self,tag):
        if tag=='details': self.depth-=1
    def handle_data(self,text):
        if 'Очередь выросла со 100 до 140' in text: self.sample_depth=self.depth
        if 'Какое решение вы подпишете сегодня?' in text: self.prompt_depth=self.depth
        if 'Подготовьте письмо по собственной сводной' in text: self.brief_depth=self.depth
chapter=root/'content/ch13'
files=sorted(chapter.glob('*.md'))
task_sources=[p for p in files if p.stem not in ('intro','test')]
lessons={p.stem:build.parse_lesson(p) for p in task_sources}
result['tasks_per_lesson']={k:len(l['tasks']) for k,l in lessons.items()}
assert sum(result['tasks_per_lesson'].values())==65
doc=lessons['05-project']['theory'];disclosure=Disclosure(); disclosure.feed(doc)
assert disclosure.brief_depth==0 and disclosure.prompt_depth==0 and disclosure.sample_depth==1
assert doc.index('Подготовьте письмо')<doc.index('Какое решение вы подпишете сегодня?')<doc.index('Очередь выросла со 100 до 140')
result['project_visible_before_tasks']={'brief_in_details':disclosure.brief_depth,'question_in_details':disclosure.prompt_depth,'sample_in_details':disclosure.sample_depth}
figs=[identifier for p in task_sources for identifier in re.findall(r'^::: figure ([\w-]+)',p.read_text(),re.M)]
assert len(figs)==len(set(figs))==19
for key in figs: ET.parse(root/f'content/figures/{key}.svg')
result['verified_svg']=figs
result['notebook_code']={}
for path in sorted((root/'site/notebooks/extra').glob('ch13-*.ipynb')):
    def code(blob):
        nb=json.loads(blob)
        return [cell for cell in nb['cells'] if cell['cell_type']=='code']
    def rawcells(blob):
        # Course notebook JSON uses this exact serialization for complete cell objects.
        # Also check that the actual raw byte span of each serialized complete cell exists.
        cells=code(blob); chunks=[]
        for cell in cells:
            single=json.dumps(cell,ensure_ascii=False,indent=1)
            piece=('  '+single.replace('\n','\n  ')).encode()
            assert piece in blob
            chunks.append(piece)
        return chunks
    a,b=rawcells(original(path)),rawcells(path.read_bytes())
    assert a==b
    result['notebook_code'][path.name]={'count':len(a),'sha256_raw_complete_cells':digest(b''.join(a))}
source='\n'.join(p.read_text() for p in task_sources+[chapter/'intro.md'])
for obsolete in ('разметка трёх сотрудников','на настоящей разметке','тему для них поставила старшая аналитик','Это подтверждает историю из урока','обрезает середину списка','разница меньше разброса — не выигрыш','знак прироста сохраняется автоматически','единицы процентов','настоящих 10 % — ложные срабатывания'):
    assert obsolete.casefold() not in source.casefold(),obsolete
assert 'temperature = 0' not in (root/'content/figures/llm-label-flow.svg').read_text()
result['target_clarifications']={
    'simulated_annotators':'три учебных профиля' in source,
    'gold_copied':'получены копированием' in source,
    'binary_and_six_topics':'другая цель — одна из шести тем' in source,
    'closed_schema':'шести тем' in source,
    'paired_interval':'от −0,675 до +14,675' in source,
    'stable_direction':'стабильны и TPR > FPR' in source,
    'opposite_direction':'TPR < FPR направление обратное' in source}
assert all(result['target_clarifications'].values())
print(json.dumps(result,indent=2,ensure_ascii=False))
