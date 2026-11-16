# Candidate replacement from ax_of onward; preceding independent cg/share stay unchanged.
from matplotlib.collections import PathCollection as _PC
ax=ax_of(0)
ax.figure.canvas.draw()
assert ax.get_visible() and ax.figure.get_visible() and ax.axison and ax.xaxis.get_visible() and ax.yaxis.get_visible(), 'Покажите сам график и обе оси.'
for _label in (ax.xaxis.label,ax.yaxis.label):
    assert _label.get_visible() and _to_rgba(_label.get_color(),alpha=_label.get_alpha())[3]>0, 'Подписи осей должны быть видимыми.'
assert ax.get_xlabel()=='доля гостей с бонусом' and ax.get_ylabel()=='доля пойманных уходящих', 'Проверьте подписи осей из условия.'
assert min(ax.get_xlim())<=1e-8 and max(ax.get_xlim())>=1-1e-8 and min(ax.get_ylim())<=1e-8 and max(ax.get_ylim())>=1-1e-8, 'Покажите обе доли от 0 до 1.'
_box,_canvas=ax.get_window_extent(),ax.figure.bbox
assert _box.x0>=_canvas.x0-1 and _box.y0>=_canvas.y0-1 and _box.x1<=_canvas.x1+1 and _box.y1<=_canvas.y1+1, 'Область графика должна помещаться на рисунке.'
_series=[]
for _line in ax.lines:
    if not _line.get_visible():continue
    _alpha=_line.get_alpha()
    _stroke=(_line.get_linewidth()>0 and _line.get_linestyle() not in ('None','none','',' ') and _to_rgba(_line.get_color(),alpha=_alpha)[3]>0)
    _face=(_line.get_fillstyle()!='none' and _to_rgba(_line.get_markerfacecolor(),alpha=_alpha)[3]>0)
    _edge=(_line.get_markeredgewidth()>0 and _to_rgba(_line.get_markeredgecolor(),alpha=_alpha)[3]>0)
    _marker=(_line.get_marker() not in ('None','none','',' ',None) and _line.get_markersize()>0 and (_face or _edge))
    if not (_stroke or _marker):continue
    _xy=_np.c_[_line.get_xdata(),_line.get_ydata()].astype(float)
    _xy=ax.transData.inverted().transform(_line.get_transform().transform(_xy))
    _series.append((_xy,_stroke))
for _col in ax.collections:
    if not isinstance(_col,_PC) or not _col.get_visible() or (_col.get_alpha() is not None and _col.get_alpha()<=0):continue
    _xy=_np.asarray(_col.get_offsets(),dtype=float)
    _n=len(_xy)
    if not _n:continue
    def _broadcast(_v):
        _v=_np.asarray(_v)
        return _np.resize(_v,_n) if len(_v) else _np.zeros(_n)
    _fc,_ec=_col.get_facecolors(),_col.get_edgecolors()
    _face=_broadcast(_fc[:,3] if len(_fc) else [])>0
    _edge=(_broadcast(_ec[:,3] if len(_ec) else [])>0)&(_broadcast(_col.get_linewidths())>0)
    _shown=(_face|_edge)&(_broadcast(_col.get_sizes())>0)
    _xy=ax.transData.inverted().transform(_col.get_offset_transform().transform(_xy[_shown]))
    _series.append((_xy,False))
_model=_diagonal=False
for _xy,_ordered in _series:
    if _xy.ndim!=2 or _xy.shape[1]!=2 or len(_xy)<2 or not _np.isfinite(_xy).all():continue
    if not _ordered:_xy=_xy[_np.lexsort((_xy[:,1],_xy[:,0]))]
    elif _xy[0,0]>_xy[-1,0]:_xy=_xy[::-1]
    _x,_y=_xy[:,0],_xy[:,1]
    if not (_np.diff(_x)>0).all():continue
    _curve=_xy[1:] if len(_xy)==len(cg)+1 and _np.allclose(_xy[0],[0,0],rtol=0,atol=1e-8) else _xy
    if len(_curve)==len(cg) and _np.allclose(_curve,_np.c_[share,cg],rtol=0,atol=1e-8):_model=True
    if _np.allclose(_x,_y,rtol=0,atol=1e-8) and _x[0]<=1e-8 and _x[-1]>=1-1e-8:_diagonal=True
assert _model, 'Нужна видимая кривая модели с верными парами долей для каждого числа выбранных гостей. Линии, маркеры и scatter допустимы.'
assert _diagonal, 'Нужна видимая диагональ случайного выбора от (0,0) до (1,1).'
assert close(need('at10'),round(cg[59],3)), 'at10: доля уходящих среди первых 60 гостей по убыванию риска.'
