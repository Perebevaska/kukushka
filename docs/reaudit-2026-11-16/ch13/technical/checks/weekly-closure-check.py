import pandas as _pd
n0 = need('n', _pd.DataFrame).copy()
n0['week'] = n0['date'].dt.to_period('W').dt.start_time
w = n0.pivot_table(index='week', columns='shop_id', values='neg', aggfunc='mean')
got = need('weekly', _pd.DataFrame)
assert got.shape == w.shape, f'weekly.shape = {got.shape}, а нужно {w.shape}.'
assert got.index.is_unique and got.columns.is_unique and set(got.index)==set(w.index) and set(got.columns)==set(w.columns), 'weekly: сохраните уникальные даты недель и точки.'
assert ((got.reindex(index=w.index,columns=w.columns).values-w.values)**2).max()<1e-12, 'Доли должны соответствовать своей неделе и точке.' 
_shop=need('focus_shop')
assert _shop in w.columns, 'Выберите точку из weekly.'
jw = w[_shop].diff().idxmax()
assert _pd.Timestamp(need('jump_week')) == jw, f'jump_week = {need("jump_week")}, а нужно {jw.date()}.'
sm = round(float(w.loc[w.index < jw, _shop].max()), 3)
assert close(need('sept_max'), sm, 0.0015), f'sept_max = {need("sept_max")}, а нужно {sm}.'

import numpy as _np
import matplotlib.dates as _md
from matplotlib.container import BarContainer as _BarContainer
_expected_dates = list(w.index)
_expected_values = w[_shop].to_numpy()
def _calendar_values(x, complete=True):
    values=list(x)
    if not values: return None
    candidates=[]
    try: candidates.append([_pd.Timestamp(v.end_time).normalize() if isinstance(v,_pd.Period) else _pd.Timestamp(v).normalize() for v in values])
    except (ValueError,TypeError,OverflowError): pass
    try: candidates.append([_pd.Timestamp(_md.num2date(float(v))).tz_localize(None).normalize() for v in values])
    except (ValueError,TypeError,OverflowError): pass
    for dates in candidates:
        if complete and len(dates)==len(_expected_dates) and set(dates)==set(_expected_dates): return dates
        if not complete and all(date in _expected_dates for date in dates): return dates
    return None
def _matches_plot(x,y,shop=_shop,complete=True):
    dates=_calendar_values(x,complete=complete)
    if dates is None: return False
    try:
        values=_np.asarray(y,dtype=float)
        expected=w.loc[dates,shop].to_numpy()
        return values.shape==expected.shape and _np.allclose(values,expected,atol=1e-6,rtol=0)
    except (ValueError,TypeError): return False
_plot_ok=False
for _fig in figs:
    for _ax in _fig.axes:
        _labels=' '.join([_ax.get_title(),*[_t.get_text() for _t in (_ax.get_legend().texts if _ax.get_legend() else [])]])
        _units=_ax.get_ylabel().lower()
        _mentioned_shops={str(_key) for _key in w.columns if str(_key) in _labels}
        if _mentioned_shops and _shop not in _mentioned_shops: continue
        if _units and not any(_unit in _units for _unit in ['дол','share','fraction']): continue
        for _line in _ax.lines:
            _named_shop=_line.get_label()
            if _named_shop in w.columns:
                assert _matches_plot(_line.get_xdata(orig=True),_line.get_ydata(),shop=_named_shop,complete=False), 'Каждая серия с названием точки должна показывать её действительные доли по датам, включая выделенную линию.'
            if _matches_plot(_line.get_xdata(orig=True),_line.get_ydata()): _plot_ok=True
        for _container in _ax.containers:
            if isinstance(_container,_BarContainer):
                _named_shop=_container.get_label()
                if _named_shop in w.columns:
                    assert _matches_plot([b.get_x()+b.get_width()/2 for b in _container.patches],[b.get_height() for b in _container.patches],shop=_named_shop,complete=False), 'Каждая серия столбцов с названием точки должна показывать её действительные доли по датам.'
                if _matches_plot([b.get_x()+b.get_width()/2 for b in _container.patches],[b.get_height() for b in _container.patches]): _plot_ok=True
assert _plot_ok, 'Покажите недельные доли выбранной точки по реальным датам; подписи, если они есть, должны сохранять долю и выбранную точку. Подойдёт линия или столбцы.'