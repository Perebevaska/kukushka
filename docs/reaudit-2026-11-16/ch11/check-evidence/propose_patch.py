"""Materialize one reviewable proposal; never modifies course sources."""
import copy,json,difflib,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
if (HERE/'after-snapshot.json').exists():
    raise SystemExit('Actual after snapshot is frozen; proposal.patch and proposal-tasks.json already preserve the proposal. Do not overwrite actual after-tasks.json.')
SNAPSHOT=Path('/private/tmp/kuch11round/original')
original=json.loads((HERE/'before-tasks.json').read_text());after=copy.deepcopy(original)
for t in after:
 if t['id']=='collapse':
  t['check'] += "\nassert _np.asarray(need('two_layers')).shape == (5, 2) and _np.allclose(need('two_layers'), (X0 @ A) @ B), 'two_layers — результат двух линейных слоёв для X из заготовки.'"
 if t['id']=='float32':
  t['check'] += "\nassert _np.array_equal(x32, _X.astype(_np.float32)), 'X32 должна сохранять значения всех клеток X64 после преобразования во float32.'"
 if t['id']=='loss-curve':
  t['check'] = t['check'].replace("import pandas as _pd", "import numpy as _np\nimport pandas as _pd",1)
  t['check'] += "\nassert _np.asarray(cv).shape == (len(lc),) and _np.allclose(cv, lc, rtol=1e-7, atol=1e-9), 'В curve нужны реальные потери каждой эпохи из loss_curve_, в исходном порядке.'"
 if t['id']=='epoch-gap':
  t['check'] += "\nassert _np.asarray(need('auc_train')).shape == (150,) and _np.allclose(need('auc_train'), tr, atol=1e-9, rtol=1e-7), 'auc_train — AUC на обучении после каждой из 150 эпох, без округления.'"
  t['check']=t['check'].replace('auc_validation — AUC на тесте','auc_validation — AUC на валидации')
 if t['id']=='zero-grad':
  t['check'] += """
for _zero in (True, False):
    _want_w, _want_grad, _want_losses = 5.0, 0.0, []
    for _step in range(4):
        if _zero:
            _want_grad = 0.0
        _prediction = _want_w * k0
        _want_losses.append(float(_np.mean((_prediction - m0) ** 2)))
        _want_grad += _np.mean(2 * (_prediction - m0) * k0)
        _want_w -= 0.02 * _want_grad
    _got_w, _got_losses = f(_zero, lr=0.02, steps=4)
    assert _np.asarray(_got_losses).shape == (4,) and _np.allclose(_got_losses, _want_losses) and close(_got_w, _want_w, 1e-8), 'run должна учитывать переданные lr и steps; длина истории равна steps, в ней потери до каждого шага.'
""".rstrip()
 if t['id']=='blur-transfer':
  t['setup']=t['setup'].replace('dict(images=val_images,proba=val_proba,target=val_target), dict(images=blind_images,proba=blind_proba)', 'dict(images=val_images.copy(),proba=val_proba.copy(),target=val_target.copy()), dict(images=blind_images.copy(),proba=blind_proba.copy())')
  t['check'] += '''
_outside = _np.flatnonzero(errors & ~_np.isin(_np.arange(len(errors)), list(_blur_state['queue'])))
_position = need('missed_example_position')
if len(_outside):
    assert isinstance(_position, (int, _np.integer)) and int(_position) in _outside, 'missed_example_position — целая позиция ошибочной цифры вне сохранённой очереди.'
else:
    assert _position is None, 'Если ошибок вне очереди нет, missed_example_position=None.'
'''.rstrip()
  t['solution'] += '''
_outside = np.flatnonzero(errors & ~np.isin(np.arange(len(errors)), queue))
missed_example_position = int(_outside[0]) if len(_outside) else None
print("Пример ошибки вне очереди:", missed_example_position)
'''.rstrip()
patch=[]
for lesson in sorted({x['lesson'] for x in original}):
 path=Path('content')/(lesson+'.md');old=(SNAPSHOT/path).read_text();new=old
 for src,dst in zip(original,after):
  if src['lesson']!=lesson:continue
  marker='## task: '+src['id']+' |';a=new.index(marker);b=new.find('\n## task: ',a+1);b=len(new) if b==-1 else b
  block=new[a:b]
  for field in ['setup','check','solution']:
   if src[field]!=dst[field]:
    assert block.count(src[field])==1,(lesson,src['id'],field,block.count(src[field]))
    block=block.replace(src[field],dst[field],1)
  if src['id']=='blur-transfer':
   old_sentence='Назовите одну позицию с ошибкой вне очереди, если такая есть.'
   assert old_sentence in block
   block=block.replace(old_sentence,'В `missed_example_position` сохраните одну целую позицию с ошибкой вне очереди, если такая есть; иначе — `None`.')
  new=new[:a]+block+new[b:]
 if old!=new:patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+str(path),tofile='b/'+str(path)))
(HERE/'proposal.patch').write_text(''.join(patch))
(HERE/'after-tasks.json').write_text(json.dumps(after,ensure_ascii=False,indent=2))
(HERE/'after-programs.jsonl').write_bytes((HERE/'programs.jsonl').read_bytes())
(HERE/'expected-after-before-execution.json').write_bytes((HERE/'expected-before-execution.json').read_bytes())
(HERE/'after-frozen.sha256').write_text(''.join(hashlib.sha256((HERE/f).read_bytes()).hexdigest()+'  '+f+'\n' for f in ['after-programs.jsonl','expected-after-before-execution.json','after-tasks.json','proposal.patch']))
print('Materialized proposal only; sources unchanged; expected verdicts and programs remain literal-identical')
