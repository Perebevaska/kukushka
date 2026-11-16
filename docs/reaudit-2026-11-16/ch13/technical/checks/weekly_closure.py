from pathlib import Path
import json,hashlib,re,ast,difflib
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course');d=root/'docs/reaudit-2026-11-16/ch13/technical/checks';tasks=json.loads((d/'after-tasks.json').read_text());weekly=next(t for t in tasks if t['id']=='weekly')
# Save the actual first-after catalog and guard; results and source manifests remain immutable.
(d/'first-after-weekly-check.py').write_text(weekly['check'])
code=weekly['check'];code=code.replace('def _calendar_values(x):','def _calendar_values(x, complete=True):').replace("if len(dates)==len(_expected_dates) and set(dates)==set(_expected_dates): return dates", "if complete and len(dates)==len(_expected_dates) and set(dates)==set(_expected_dates): return dates\n        if not complete and all(date in _expected_dates for date in dates): return dates")
a=code.index('def _matches_plot(');b=code.index('_plot_ok=False',a)
code=code[:a]+'''def _matches_plot(x,y,shop=_shop,complete=True):
    dates=_calendar_values(x,complete=complete)
    if dates is None: return False
    try:
        values=_np.asarray(y,dtype=float)
        expected=w.loc[dates,shop].to_numpy()
        return values.shape==expected.shape and _np.allclose(values,expected,atol=1e-6,rtol=0)
    except (ValueError,TypeError): return False
''' +code[b:]
code=code.replace("for _line in _ax.lines:\n            if _matches_plot(_line.get_xdata(orig=True),_line.get_ydata()): _plot_ok=True", "for _line in _ax.lines:\n            _named_shop=_line.get_label()\n            if _named_shop in w.columns:\n                assert _matches_plot(_line.get_xdata(orig=True),_line.get_ydata(),shop=_named_shop,complete=False), 'Каждая серия с названием точки должна показывать её действительные доли по датам, включая выделенную линию.'\n            if _matches_plot(_line.get_xdata(orig=True),_line.get_ydata()): _plot_ok=True")
code=code.replace("if isinstance(_container,_BarContainer):\n                if _matches_plot", "if isinstance(_container,_BarContainer):\n                _named_shop=_container.get_label()\n                if _named_shop in w.columns:\n                    assert _matches_plot([b.get_x()+b.get_width()/2 for b in _container.patches],[b.get_height() for b in _container.patches],shop=_named_shop,complete=False), 'Каждая серия столбцов с названием точки должна показывать её действительные доли по датам.'\n                if _matches_plot")
ast.parse(code);assert code!=weekly['check'];(d/'weekly-closure-check.py').write_text(code)
# Programs selected explicitly before execution; originals remain literal where selected.
orig=list(map(json.loads,(d/'programs.jsonl').read_text().splitlines()));cases=[]
def emit(label,src,expected,description):
 ast.parse(src);cases.append(dict(lesson='ch13/05-project',task='weekly',label=label,code=src,expected=expected,description=description,code_sha256=hashlib.sha256(src.encode()).hexdigest()))
for index in [186,187,219,218]:
 r=orig[index];emit('literal235-'+str(index),r['code'],r['expected'],r['description'])
s=weekly['solution'];prefix=s+'\nplt.close("all")\nfig,ax=plt.subplots()\n'
double=prefix+'ax.plot(weekly.index,weekly[focus_shop],label=focus_shop)\nax.plot(weekly.index,weekly[focus_shop],label=focus_shop,linestyle="--")\n'
emit('two-correct-focus-lines',double,True,'Обе линии с названием выбранной точки правильны; подписи осей и легенда не обязательны')
emit('second-focus-line-wrong',double+'ax.lines[-1].set_ydata(weekly[focus_shop].to_numpy()+.1)\n',False,'Одна подписанная линия верна, вторая завышена на .1')
bar=prefix+'ax.bar(weekly.index,weekly[focus_shop],label=focus_shop,width=5)\n'
emit('bar-correct',bar,True,'Корректная столбчатая серия дат/долей')
emit('bar-one-coordinate-wrong',bar+'ax.patches[3].set_height(0)\n',False,'Один подписанный столбец искажён')
review=json.loads((root/'docs/reaudit-2026-11-16/ch13/fixes/reviewer-evidence/cases-before.json').read_text())
for id in ['R12','R13']:
 r=next(r for r in review if r['id']==id);emit('reviewer-'+id,r['code'],r['expected'],r['reason'])
other=prefix+'other=next(shop for shop in weekly.columns if shop!=focus_shop)\nax.plot(weekly.index,weekly[focus_shop],label=focus_shop)\nax.plot(weekly.index,weekly[other],label=other)\n'
emit('two-different-correct-shops',other,True,'Две однозначно подписанные точки, обе серии верны')
emit('other-shop-label-wrong-values',other+'ax.lines[-1].set_ydata(weekly[focus_shop].to_numpy())\n',False,'Чужая подпись точки при значениях выбранной')
partial=prefix+'ax.plot(weekly.index,weekly[focus_shop],label=focus_shop)\nax.plot([weekly.index[2]],[weekly[focus_shop].iloc[2]],marker="o",label=focus_shop)\n'
emit('valid-annotated-point',partial,True,'Частичная подписанная серия как верная аннотация к полной динамике')
emit('wrong-annotated-point',partial+'ax.lines[-1].set_ydata([weekly[focus_shop].iloc[2]+.1])\n',False,'Подписанная аннотация содержит неверное значение')
(d/'weekly-closure-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in cases));(d/'weekly-closure-freeze.json').write_text(json.dumps({'program_count':len(cases),'program_sha256':hashlib.sha256((d/'weekly-closure-programs.jsonl').read_bytes()).hexdigest(),'first_after_task65_sha256':hashlib.sha256((d/'after-tasks.json').read_bytes()).hexdigest(),'first_after_weekly_check_sha256':hashlib.sha256(weekly['check'].encode()).hexdigest(),'candidate_weekly_check_sha256':hashlib.sha256(code.encode()).hexdigest()},indent=2))
# Apply only weekly/check to actual source; preserve64 other tasks and three other weekly code fields.
source=root/'content/ch13/05-project.md';old=source.read_text();parts=re.split(r'(?m)(?=^## task: )',old);new=parts[0]
for part in parts[1:]:
 if part.startswith('## task: weekly |'):
  pattern=r'(?ms)(^### check\s*\n```python[^\n]*\n)(.*?)(\n```\s*(?=\n### |\Z))';m=re.search(pattern,part);assert m and m[2].strip()==weekly['check'].strip()
  part,n=re.subn(pattern,lambda m:m[1]+code.rstrip()+m[3],part,count=1);assert n==1
 new+=part
source.write_text(new);(d/'weekly-closure-applied.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/content/ch13/05-project.md',tofile='b/content/ch13/05-project.md')))
# Proof is compared to the actual first-after export, not the original proposal.
proof={'unchanged64x4':True,'only_weekly_check_changed':True,'cards':[]}
for source in sorted((root/'content/ch13').glob('*.md')):
 text=source.read_text()
 for part in re.split(r'(?m)(?=^## task: )',text)[1:]:
  id=part.split(' |',1)[0].split('## task: ')[1];t=next(t for t in tasks if t['lesson']=='ch13/'+source.stem and t['id']==id);fields={}
  for field in ['setup','starter','check','solution']:
   m=re.search(r'(?ms)^### '+field+r'\s*\n```python[^\n]*\n(.*?)\n```',part);actual=m[1].strip() if m else '';ast.parse(actual)
   same=actual==t.get(field,'').strip();fields[field]={'unchanged_from_first_after':same,'sha256':hashlib.sha256(actual.encode()).hexdigest()}
   assert same or (id=='weekly' and field=='check'),(id,field)
  proof['cards'].append(dict(lesson=t['lesson'],id=id,fields=fields))
assert len(proof['cards'])==65
(d/'weekly-closure-source-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print('APPLIED only weekly/check;64x4 unchanged;closure frozen',len(cases),'cases')
