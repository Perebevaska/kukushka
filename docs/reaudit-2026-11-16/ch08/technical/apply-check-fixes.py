"""Apply the critic's three argument checks and the visible gains contract."""
import json,re
from pathlib import Path
D=Path(__file__).resolve().parents[1];ROOT=D.parents[2]
additions=json.loads((D/'check-evidence/candidate-check-additions.json').read_text())
original=json.loads((D/'technical/baseline-export.json').read_text())
checks={r['lesson'].removeprefix('ch08/')+'/'+r['id']:r['check'] for r in original if r['kind']=='task'}
for key in ('01-value/p-profit','04-monitoring/p-monitor','05-explain/p-pd'):
 lesson,id=key.split('/')
 p=ROOT/f'content/ch08/{lesson}.md';text=p.read_text()
 prefix,task=text.split('## task: '+id+' |',1)
 body,separator,tail=task.partition('\n## task: ')
 marker='### check\n';before,check=body.split(marker,1)
 current,next_section,rest=check.partition('\n### ')
 addition=additions[key].strip()
 code=checks[key].rstrip()+'\n'+addition
 p.write_text(prefix+'## task: '+id+' |'+before+marker+'```python\n'+code+'\n```\n'+next_section+rest+separator+tail)
p=ROOT/'content/ch08/02-budget.md';text=p.read_text();prefix,task=text.split('## task: gains-plot |',1)
body,separator,tail=task.partition('\n## task: ')
before,check=body.split('### check\n',1);current,next_section,rest=check.partition('\n### ')
# Reference predictions and data pairs remain independent of the learner's plot.
reference=checks['02-budget/gains-plot'].split('ax = ax_of(0)',1)[0]
replacement=(D/'check-evidence/gains-candidate.py').read_text().split('\n',1)[1]
replacement=replacement.replace("if _np.allclose(_x,_y,rtol=0,atol=1e-8) and _x[0]<=1e-8 and _x[-1]>=1-1e-8:_diagonal=True", "if _ordered and _np.allclose(_x,_y,rtol=0,atol=1e-8) and _x[0]<=1e-8 and _x[-1]>=1-1e-8:_diagonal=True")
p.write_text(prefix+'## task: gains-plot |'+before+'### check\n```python\n'+reference+replacement.rstrip()+'\n```\n'+next_section+rest+separator+tail)
print('Applied four checker changes; published site unchanged until build.')
