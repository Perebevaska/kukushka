"""Dry-run by default. --apply changes only two previously identified check blocks."""
from pathlib import Path
import argparse,difflib,re,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
changes={}
def check(rel,task,transform):
 path=ROOT/rel;old=path.read_text();start=old.index('## task: '+task+' |');end=old.find('\n## task:',start+1)
 if end<0:end=len(old)
 block=old[start:end];cs=block.index('### check\n```python\n')+len('### check\n```python\n');ce=block.index('\n```',cs)
 body=block[cs:ce];newbody=transform(body);assert body!=newbody
 compile(newbody,rel+':'+task+':check','exec')
 block=block[:cs]+newbody+block[ce:];changes[path]=(old,old[:start]+block+old[end:])
check('content/ch10/04-tuning.md','train-vs-test',lambda b:b+r'''
for _name, _reference_curve in [('tr', tr), ('te', te)]:
    _submitted_curve = _np.asarray(need(_name), dtype=float)
    assert (_submitted_curve.shape == (400,)
            and _np.allclose(_submitted_curve, _reference_curve, rtol=1e-6, atol=1e-6)), f'{_name}: нужны все 400 MAE после каждого дерева на соответствующей выборке, в порядке от 1 до 400. Правильных итоговых чисел недостаточно — проверьте сам массив.'
''')
def tune(b):
 start=b.index("g = need('grid', _pd.DataFrame)")
 return b[:start]+r'''g = need('grid', _pd.DataFrame)
assert {'lr', 'depth', 'n_iter', 'val_mae'} <= set(g.columns), 'В grid нужны столбцы lr, depth, n_iter и val_mae.'
assert len(g) == 6, f'В grid {len(g)} строк, нужно 6.'
def _grid_key(row):
    return (float(row['lr']), None if _pd.isna(row['depth']) else float(row['depth']))
_expected_rows = {(lr, md): (k, v) for lr, md, k, v in rows}
_submitted_keys = [_grid_key(row) for _, row in g.iterrows()]
assert len(set(_submitted_keys)) == 6 and set(_submitted_keys) == set(_expected_rows), 'grid: нужны ровно шесть разных пар lr из [0.05, 0.1] и depth из [3, 6, None]; каждая строка должна сохранять параметры своего расчёта. Порядок строк может быть любым.'
for _, row in g.iterrows():
    _key = _grid_key(row)
    _k, _v = _expected_rows[_key]
    assert row['n_iter'] == _k and close(row['val_mae'], _v, 0.01), f'lr={_key[0]}, depth={_key[1]}: n_iter и val_mae должны относиться к этой паре параметров.'
b = min(rows, key=lambda r: r[3])
assert close(need('val_mae'), round(b[3], 2), 0.011), 'Сохраните MAE лучшей строки на апреле–июне.'
_submitted_best = need('best', _pd.Series)
assert (_grid_key(_submitted_best) == (b[0], b[1])
        and _submitted_best['n_iter'] == b[2]
        and close(_submitted_best['val_mae'], b[3], 0.01)), 'best должна сохранять параметры, число деревьев и ошибку лучшей строки grid; не меняйте её lr/depth после расчёта.'
'''
check('content/ch10/05-project.md','tune',tune)
patch='';manifest=[]
for path,(old,new) in changes.items():
 rel=str(path.relative_to(ROOT));patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel,tofile=rel))
 manifest.append(dict(path=rel,before_sha256=hashlib.sha256(old.encode()).hexdigest(),after_sha256=hashlib.sha256(new.encode()).hexdigest()))
(HERE/'closure-fixes.patch').write_text(patch)
(HERE/'closure-fixes-manifest.json').write_text(json.dumps(dict(applied=a.apply,files=manifest,scope='two check blocks only',conditions_changed=False),ensure_ascii=False,indent=2))
if a.apply:
 for path,(_,new) in changes.items():path.write_text(new)
print(('Applied' if a.apply else 'Prepared')+' two check-only fixes; no condition changes, no ML execution.')
