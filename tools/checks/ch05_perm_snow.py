"""Validate the actual binary permutation distribution, not just its center."""
import numpy as _np
import pandas as _pd
from scipy.stats import hypergeom as _hypergeom

_frame = _pd.read_csv('deliveries.csv')
_frame = _frame[_frame.actual_min.between(1, 299)]
_late = (_frame.actual_min > _frame.promised_min).to_numpy()
_snow = _frame.weather.eq('снег').to_numpy()
_n1, _n0, _total = int(_snow.sum()), int((~_snow).sum()), int(_late.sum())
_observed = _late[_snow].mean() - _late[~_snow].mean()
_dd = _np.asarray(need('diffs'), dtype=float)
assert _dd.shape == (3000,) and _np.isfinite(_dd).all(), 'diffs — массив 3000 конечных перестановочных разниц.'
# Each possible difference corresponds to an integer number of late snow orders.
_counts_float = (_dd + _total / _n0) / (1 / _n1 + 1 / _n0)
_counts = _np.rint(_counts_float).astype(int)
_min, _max = max(0, _total - _n0), min(_n1, _total)
assert _np.allclose(_counts_float, _counts, rtol=0, atol=1e-8) and (_counts >= _min).all() and (_counts <= _max).all(), 'diffs должны получаться перестановкой групп с сохранением их размеров; проверьте разницу долей, а не п.п. или нулевую заготовку.'
_support = _np.arange(_min, _max + 1)
_ecdf = _np.searchsorted(_np.sort(_counts), _support, side='right') / len(_dd)
_cdf = _hypergeom.cdf(_support, _n1 + _n0, _total, _n1)
assert _np.max(_np.abs(_ecdf - _cdf)) < .06, 'Распределение diffs не соответствует случайным перестановкам этих доставок; одного среднего около нуля недостаточно.'
_hits = int(_np.count_nonzero(_np.abs(_dd) >= abs(_observed) - 1e-12))
_want = (_hits + 1) / (len(_dd) + 1)
_p = float(need('p_value'))
assert _np.isfinite(_p) and 0 < _p <= 1, 'Для конечного Монте-Карло p_value положительно: используйте (k + 1) / (B + 1), а не 0 при k = 0.'
assert abs(_p - _want) < 1e-12, f'p_value должно следовать из ваших diffs: ({_hits} + 1) / 3001 = {_want:.8f}; не округляйте сохранённое p.'
