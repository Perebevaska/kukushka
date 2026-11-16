"""Check real inputs, finite Monte Carlo budgets and exact small distributions."""
import math as _math
import numpy as _np
import pandas as _pd
from itertools import combinations as _combinations

_f = need('perm_test')

def _pair(result, observed, label):
    assert len(result) == 2, f'{label}: верните пару (разница средних, p-value).'
    difference, probability = map(float, result)
    assert _np.isfinite(difference) and abs(difference - observed) < 1e-10, f'{label}: разница — среднее a минус среднее b, а не подставленное число.'
    assert _np.isfinite(probability) and 0 < probability <= 1, f'{label}: p должно быть конечным и положительным; ноль попаданий в MC не означает p = 0.'
    return probability

def _exact(a, b):
    pooled, n = _np.r_[a, b], len(a)
    observed = a.mean() - b.mean()
    hits = total = 0
    for indices in _combinations(range(len(pooled)), n):
        mask = _np.zeros(len(pooled), dtype=bool)
        mask[list(indices)] = True
        d = pooled[mask].mean() - pooled[~mask].mean()
        hits += abs(d) >= abs(observed) - 1e-12
        total += 1
    return hits / total

def _small(a, b, budget, seed, label):
    exact = _exact(a, b)
    p = _pair(_f(a.copy(), b.copy(), n_perm=budget, seed=seed), a.mean() - b.mean(), label)
    # Exact enumeration is accepted without +1. Independent corrected MC need
    # not reproduce the reference RNG sequence (six binomial standard errors).
    tolerance = 6 * _math.sqrt(exact * (1 - exact) / budget) + 2 / (budget + 1)
    assert abs(p - exact) <= tolerance, f'{label}: двусторонняя перестановочная вероятность около {exact:.6f}, а у вас {p:.6f}.'
    repeat = _f(a.copy(), b.copy(), n_perm=budget, seed=seed)
    assert abs(float(repeat[1]) - p) < 1e-12, f'{label}: при том же seed результат должен воспроизводиться.'

_small(_np.array([1., 2, 3, 4, 5]), _np.array([1., 2, 3, 4, 5]), 500, 0, 'Одинаковые массивы')
_small(_np.array([1., 1, 0]), _np.array([0., 0, 0]), 4000, 17, 'Полный игрушечный хвост 8/20')
_small(_np.array([3., 4, 6]), _np.array([1., 2, 5, 7]), 3000, 9, 'Неравные размеры групп')
# Complete separation has exactly two extreme assignments among C(24, 12).
_a, _b = _np.arange(12., dtype=float), _np.arange(100., 112.)
_exact_far = 2 / _math.comb(24, 12)
for _budget in (13, 2000):
    _p = _pair(_f(_a.copy(), _b.copy(), n_perm=_budget, seed=0), -100., f'Редкий хвост, B={_budget}')
    if abs(_p - _exact_far) > 1e-12:
        _floor = 1 / (_budget + 1)
        _tolerance = 6 * _math.sqrt(_exact_far * (1 - _exact_far) / _budget)
        assert _floor - 1e-12 <= _p <= _exact_far + _tolerance + _floor, f'B={_budget}: для MC при нуле попаданий p=1/(B+1); точный хвост {_exact_far:.10g} допустим при полном точном расчёте.'

_frame = _pd.read_csv('deliveries.csv')
_ok = _frame[_frame.actual_min.between(1, 299)]
_auto = _ok.loc[_ok.courier.eq('авто'), 'actual_min'].to_numpy(float)
_velo = _ok.loc[_ok.courier.eq('вело'), 'actual_min'].to_numpy(float)
_observed = _auto.mean() - _velo.mean()
_res_p = _pair(need('res'), _observed, 'res на авто и вело')
_repeat_p = _pair(_f(_auto.copy(), _velo.copy(), n_perm=2000, seed=0), _observed, 'Повтор авто и вело')
assert abs(_res_p - _repeat_p) < 1e-12, 'res — результат вашей функции на авто/вело с n_perm=2000 и seed=0; не заменяйте сохранённый ответ.'
_rng = _np.random.default_rng(762)
_pool, _n = _np.r_[_auto, _velo], len(_auto)
_hits = 0
for _ in range(8000):
    _perm = _rng.permutation(_pool)
    _hits += abs(_perm[:_n].mean() - _perm[_n:].mean()) >= abs(_observed) - 1e-12
_ref = (_hits + 1) / 8001
_tolerance = 6 * _math.sqrt(_ref * (1 - _ref) / 2000) + 6 * _math.sqrt(_ref * (1 - _ref) / 8000)
assert abs(_res_p - _ref) <= _tolerance, f'res: p около {_ref:.4f}; считайте перестановочную разницу средних этих массивов.'
