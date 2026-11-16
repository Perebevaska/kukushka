"""Close the reviewer's rendered-path, marker-subsampling and float-grid cases."""
from pathlib import Path
D=Path(__file__).resolve().parents[1];ROOT=D.parents[2]
def change(lesson,task,fn):
 p=ROOT/f'content/ch08/{lesson}.md';s=p.read_text();before,tail=s.split('## task: '+task+' |',1)
 card,sep,after=tail.partition('\n## task: ');a,b=card.split('### check\n```python\n',1);check,c=b.split('\n```',1)
 revised=fn(check);assert revised!=check
 p.write_text(before+'## task: '+task+' |'+a+'### check\n```python\n'+revised+'\n```'+c+sep+after)
def gains(s):
 s=s.replace('from matplotlib.collections import PathCollection as _PC','from matplotlib.collections import PathCollection as _PC\nfrom matplotlib.lines import _mark_every_path\nfrom matplotlib.path import Path as _Path')
 s=s.replace('_series=[]','_series=[]\n_diagonal_paths=[]')
 old='''    _xy=_np.c_[_line.get_xdata(),_line.get_ydata()].astype(float)
    _xy=ax.transData.inverted().transform(_line.get_transform().transform(_xy))
    _series.append((_xy,_stroke))'''
 new='''    _raw=_np.c_[_line.get_xdata(),_line.get_ydata()].astype(float)
    _transform=_line.get_transform()
    if _stroke:
        _xy=ax.transData.inverted().transform(_transform.transform(_raw))
        _series.append((_xy,True))
        # drawstyle changes the rendered line path, including a stepped diagonal.
        _drawn=ax.transData.inverted().transform(_transform.transform(_line.get_path().vertices))
        _diagonal_paths.append(_drawn)
    if _marker:
        # Use the same marker-selection helper as this pinned Matplotlib renderer.
        _path=_Path(_raw)
        if _line.get_markevery() is not None:
            _path=_mark_every_path(_line.get_markevery(),_path,_transform,ax)
        _xy=ax.transData.inverted().transform(_transform.transform(_path.vertices))
        _series.append((_xy,False))'''
 assert old in s;s=s.replace(old,new)
 old='''    if _ordered and _np.allclose(_x,_y,rtol=0,atol=1e-8) and _x[0]<=1e-8 and _x[-1]>=1-1e-8:_diagonal=True'''
 new='''for _xy in _diagonal_paths:
    if _xy.ndim!=2 or _xy.shape[1]!=2 or len(_xy)<2 or not _np.isfinite(_xy).all():continue
    if _np.allclose(_xy[:,0],_xy[:,1],rtol=0,atol=1e-8) and _xy[:,0].min()<=1e-8 and _xy[:,0].max()>=1-1e-8:_diagonal=True'''
 assert old in s;s=s.replace(old,new)
 return s
def money(s):
 old='''    _frame = _frame.set_index("threshold")
    assert _frame.index.is_unique and set(_frame.index) == set(_ref.index), f"{_name}: нужна одна строка на каждый порог сетки."'''
 new='''    _values = _np.asarray(_frame["threshold"],dtype=float)
    assert len(_values)==len(_ts) and _np.isfinite(_values).all(), f"{_name}: нужна одна строка на каждый порог сетки."
    _positions = _np.abs(_values[:,None]-_ts).argmin(axis=1)
    assert len(set(_positions))==len(_ts) and _np.allclose(_values,_ts[_positions],rtol=0,atol=1e-8), f"{_name}: нужна одна строка на каждый порог сетки."
    _frame = _frame.copy()
    _frame.index = _ts[_positions]'''
 assert old in s;s=s.replace(old,new)
 old='''assert _bt in _ref.index, "Выберите порог сетки и зафиксируйте его до открытия теста."'''
 new='''_position = int(_np.abs(_ts-_bt).argmin())
assert _np.isfinite(_bt) and _np.isclose(_bt,_ts[_position],rtol=0,atol=1e-8), "Выберите порог сетки и зафиксируйте его до открытия теста."
_bt = float(_ts[_position])'''
 assert old in s;return s.replace(old,new)
def honest(s):
 old='''assert _bti == need("best_t") and _bti in _np.arange(0.02,0.41,0.02).round(2), "Перенесите тот же best_t из шага выбора по дополнительной марже."'''
 new='''_grid = _np.arange(0.02,0.41,0.02).round(2)
_position = int(_np.abs(_grid-float(_bti)).argmin())
assert _np.isfinite(_bti) and _np.isclose(_bti,need("best_t"),rtol=0,atol=1e-8) and _np.isclose(_bti,_grid[_position],rtol=0,atol=1e-8), "Перенесите тот же best_t из шага выбора по дополнительной марже."
_bti = float(_grid[_position])'''
 assert old in s;return s.replace(old,new)
change('02-budget','gains-plot',gains)
change('07-final-project','fp-money',money)
change('07-final-project','fp-honest',honest)
