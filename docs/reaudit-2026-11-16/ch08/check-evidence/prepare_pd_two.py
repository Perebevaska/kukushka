"""Prepare six targeted post-fix cases; no ML or runtime execution."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
R=H.parents[3]
source=Path(sys.argv[1] if len(sys.argv)>1 else '/private/tmp/kuch08round/final.json')
phase=sys.argv[2] if len(sys.argv)>2 else 'pd-two-final'
alltasks=[t for t in json.loads(source.read_text()) if t['lesson']=='ch08/05-explain' and t['kind']=='task' and t['id']=='pd-two']
assert len(alltasks)==1
task=alltasks[0];s=task['solution'];key='05-explain/pd-two'
old='ax.plot(grid, pd_new, marker="o", label="новички")\nax.plot(grid, pd_old, marker="o", label="остальные")'
assert s.count(old)==1
reverse=s.replace(old,'ax.plot(grid,pd_old,marker="o",label="остальные")\nax.plot(grid,pd_new,marker="o",label="новички")')
explicit=s.replace(old,'ax.plot(grid,pd_new,marker="o")\nax.plot(grid,pd_old,marker="o")')
assert explicit!=s and explicit.count('ax.legend()')==1
explicit=explicit.replace('ax.legend()','ax.legend(["новички","остальные"])')
cases=[
 ('pd-two-authored',True,s,'Две правильные подписанные линии.'),
 ('pd-two-order',True,reverse,'Порядок целых подписанных линий не влияет на результат.'),
 ('pd-two-explicit-legend',True,explicit,'Подписи легенды переданы отдельным списком.'),
 ('pd-two-zero-lines',False,s+'\nfor line in ax.lines:line.set_ydata([0]*len(grid))','Исходный доказанный контрпример: обе графические линии нулевые.'),
 ('pd-two-label-swap',False,s+'\nax.lines[0].set_label("остальные")\nax.lines[1].set_label("новички")\nax.legend()','Те же численные зависимости приписаны другим группам.'),
 ('pd-two-invisible-line',False,s+'\nax.lines[0].set_alpha(0)','Одна из двух требуемых линий отсутствует визуально.'),
]
probes=[dict(id=id,key=key,expected=expected,code=code,reason=reason)for id,expected,code,reason in cases]
(H/f'tasks-{phase}.json').write_text(json.dumps(alltasks,ensure_ascii=False,indent=2)+'\n')
(H/f'probes-{phase}.json').write_text(json.dumps(probes,ensure_ascii=False,indent=2)+'\n')
(H/f'manifest-{phase}.json').write_text(json.dumps(dict(export=str(source),export_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),check_sha256=hashlib.sha256(task['check'].encode()).hexdigest(),source_sha256=hashlib.sha256((R/'content/ch08/05-explain.md').read_bytes()).hexdigest(),probes=len(probes),expectations_written_before_run=True),ensure_ascii=False,indent=2)+'\n')
print('Prepared six targeted cases:',phase)
