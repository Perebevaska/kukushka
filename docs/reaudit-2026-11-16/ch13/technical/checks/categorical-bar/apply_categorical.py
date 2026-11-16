from pathlib import Path
import re,json,ast,hashlib,difflib,shutil
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course');d=root/'docs/reaudit-2026-11-16/ch13/technical/checks';c=d/'categorical-bar';before_tasks=json.loads((c/'tasks-before.json').read_text());t=next(t for t in before_tasks if t['id']=='weekly');old_code=t['check'];code=old_code
code=code.replace('def _calendar_values(x, complete=True):','def _calendar_values(x, complete=True, axis=None, categorical=False):')
start=code.index('    for dates in candidates:',code.index('def _calendar_values'))
code=code[:start]+'''    if categorical and axis is not None:
        try:
            locations=_np.asarray(axis.get_xticks(),dtype=float)
            labels=axis.get_xticklabels()
            mapped=[]
            for coordinate in values:
                matches=_np.flatnonzero(_np.isclose(locations,float(coordinate),rtol=0,atol=1e-8))
                if len(matches)!=1:
                    raise ValueError('Категориальный столбец должен иметь одну подпись даты на своей позиции.')
                text=labels[int(matches[0])].get_text().strip()
                mapped.append(_pd.Timestamp(text).normalize())
            candidates.append(mapped)
        except (ValueError,TypeError,OverflowError,IndexError):
            pass
''' +code[start:]
code=code.replace('def _matches_plot(x,y,shop=_shop,complete=True):','def _matches_plot(x,y,shop=_shop,complete=True,axis=None,categorical=False):').replace('dates=_calendar_values(x,complete=complete)','dates=_calendar_values(x,complete=complete,axis=axis,categorical=categorical)')
code=code.replace('for b in _container.patches],shop=_named_shop,complete=False)','for b in _container.patches],shop=_named_shop,complete=False,axis=_ax,categorical=True)').replace('for b in _container.patches]): _plot_ok=True','for b in _container.patches],axis=_ax,categorical=True): _plot_ok=True')
ast.parse(code);assert code!=old_code;assert code.count('axis=_ax,categorical=True')==2
source=root/'content/ch13/05-project.md';old=source.read_text();assert old==(c/'05-project-before.md').read_text();parts=re.split(r'(?m)(?=^## task: )',old);new=parts[0]
public='''

После вычисления `weekly` и самостоятельного выбора `focus_shop` в браузере для столбцов используйте прямой matplotlib:

```python
fig, ax = plt.subplots()
ax.bar(weekly.index.to_pydatetime(), weekly[focus_shop].to_numpy(), width=4)
ax.set(xlabel="Понедельник недели", ylabel="Доля сигналов", title=str(focus_shop))
```

В текущей браузерной версии pandas `Series.plot(kind="bar")` с `DatetimeIndex` может завершиться `ValueError` ещё до проверки. Пример выше показывает ту же зависимость через matplotlib и не выбирает точку за вас.
'''
for part in parts[1:]:
 if part.startswith('## task: weekly |'):
  pattern=r'(?ms)(^### check\s*\n```python[^\n]*\n)(.*?)(\n```\s*(?=\n### |\Z))';m=re.search(pattern,part);assert m and m[2].strip()==old_code.strip();part,n=re.subn(pattern,lambda m:m[1]+code.rstrip()+m[3],part,count=1);assert n==1
  pos=part.index('\n### setup');part=part[:pos]+public+part[pos:]
 new+=part
source.write_text(new);(c/'05-project-after.md').write_text(new);(c/'applied.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/content/ch13/05-project.md',tofile='b/content/ch13/05-project.md')))
# Exact actual source code fields, no build or notebook mutation.
after_tasks=[];proof={'unchanged64x4':True,'only_weekly_check_code_changed':True,'public_example_added':True,'cards':[]}
for f in sorted((root/'content/ch13').glob('*.md')):
 for part in re.split(r'(?m)(?=^## task: )',f.read_text())[1:]:
  id=part.split(' |',1)[0].split('## task: ')[1];original=next(t for t in before_tasks if t['lesson']=='ch13/'+f.stem and t['id']==id);actual=dict(original);fields={}
  for field in ['setup','starter','check','solution']:
   m=re.search(r'(?ms)^### '+field+r'\s*\n```python[^\n]*\n(.*?)\n```',part)
   if not m and field=='solution':m=re.search(r'(?ms)^### parsons\s*\n```python[^\n]*\n(.*?)\n```',part)
   value=m[1].strip() if m else '';ast.parse(value);same=value==original.get(field,'').strip();fields[field]={'unchanged_from_before':same,'sha256':hashlib.sha256(value.encode()).hexdigest()};assert same or (id=='weekly' and field=='check'),(id,field)
   actual[field]=value
  proof['cards'].append(dict(lesson=actual['lesson'],id=id,fields=fields));after_tasks.append(actual)
assert len(after_tasks)==65
(c/'tasks-after-source.json').write_text(json.dumps(after_tasks,ensure_ascii=False,indent=2));proof['harness_unchanged_sha256']=hashlib.sha256((root/'site/assets/harness.py').read_bytes()).hexdigest();assert (root/'site/assets/harness.py').read_bytes()==(d/'after_harness.py').read_bytes();(c/'source-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));(c/'after-source-manifest.json').write_text(json.dumps({'origin':'actual Markdown code fields after edit, before root publication/build','tasks65_sha256':hashlib.sha256((c/'tasks-after-source.json').read_bytes()).hexdigest(),'source_05project_sha256':hashlib.sha256(new.encode()).hexdigest(),'harness_sha256':proof['harness_unchanged_sha256'],'program_sha256':hashlib.sha256((c/'programs.jsonl').read_bytes()).hexdigest()},indent=2));print('APPLIED weekly/check + public example only;64x4 unchanged')
