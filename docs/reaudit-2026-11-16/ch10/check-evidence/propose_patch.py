"""Prepare two narrowly scoped check corrections; --apply is coordinator-owned."""
import argparse,difflib
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
changes={}
def append_check(file,task,addition):
 path=ROOT/'content/ch10'/file
 old=changes.get(path,path.read_text())
 start=old.index('## task: '+task+' |');end=old.find('\n## task:',start+1)
 if end<0:end=len(old)
 block=old[start:end]
 marker='### check\n```python\n';check_start=block.index(marker)+len(marker);check_end=block.index('\n```',check_start)
 block=block[:check_end]+'\n'+addition.strip()+block[check_end:]
 changes[path]=old[:start]+block+old[end:]
append_check('01-gradient.md','history',r'''
_curve = _np.asarray(need('history'), dtype=float)
_matching_lines = []
for _line in ax.lines:
    _shown = _np.asarray(_line.get_ydata(), dtype=float)
    if _shown.shape == _curve.shape and _np.allclose(_shown, _curve, rtol=1e-7, atol=1e-7):
        _matching_lines.append(_line)
assert _matching_lines, 'График должен показывать значения history после каждого шага: проверьте все 40 MSE, а не только число точек.'
''')
append_check('02-gd-many.md','decay',r'''
assert len(need('last5_const')) == 5 and len(need('last5_decay')) == 5, 'last5_const и last5_decay должны содержать ровно пять MSE — за последние пять эпох.'
''')
patch=''
for path,new in changes.items():
 old=path.read_text()
 patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(path.relative_to(ROOT)),tofile=str(path.relative_to(ROOT))))
 if a.apply:path.write_text(new)
(HERE/'proposal.patch').write_text(patch)
print('Applied' if a.apply else 'Prepared',len(changes),'check changes; conditions unchanged.')
