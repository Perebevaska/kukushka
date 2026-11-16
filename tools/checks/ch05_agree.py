"""Check the permutation distribution, then repeat the same program on a small CSV."""
import contextlib as _contextlib
import io as _io
import os as _os
import tempfile as _tempfile
import numpy as _np
import pandas as _pd
from scipy.stats import hypergeom as _hypergeom
from statsmodels.stats.proportion import proportions_ztest as _z


def _check_agreement_values(values, frame, label):
    valid = frame[frame['actual_min'].between(1, 299)]
    part = valid[valid['shop_id'].isin(['KZN-1', 'KZN-2'])]
    late = (part['actual_min'] > part['promised_min']).to_numpy()
    group = (part['shop_id'] == 'KZN-2').to_numpy()
    n_b, n_a = int(group.sum()), int((~group).sum())
    late_b, total_late = int(late[group].sum()), int(late.sum())
    observed = late[group].mean() - late[~group].mean()
    p_z = float(_z([late_b, total_late - late_b], [n_b, n_a])[1])
    # Conditioning on group sizes and total positives is exactly the distribution
    # obtained by shuffling labels, outcomes or drawing a hypergeometric count.
    counts = _np.arange(max(0, total_late - n_a), min(n_b, total_late) + 1)
    possible = counts / n_b - (total_late - counts) / n_a
    p_exact = float(_hypergeom.pmf(counts, n_a + n_b, total_late, n_b)[
        _np.abs(possible) >= abs(observed) - 1e-12].sum())
    assert all(name in values for name in ('p_z', 'p_perm', 'diff_pp')), f'{label}: сохраните p_z, p_perm и diff_pp.'
    assert _np.isfinite(float(values['p_z'])) and 0 <= float(values['p_z']) <= 1, f'{label}: p_z должна лежать от 0 до 1.'
    assert close(values['p_z'], p_z, 6e-5), f'{label}: p_z={values["p_z"]}, нужно около {p_z:.6f}.'
    assert close(values['diff_pp'], round(observed * 100, 1)), f'{label}: diff_pp — разница долей KZN-2 минус KZN-1 в п.п.'
    p_perm = float(values['p_perm'])
    assert _np.isfinite(p_perm) and 0 <= p_perm <= 1, f'{label}: p_perm должна лежать от 0 до 1.'
    # Allow statistically equivalent independent permutations and the +1 correction;
    # no particular RNG draw sequence or placement of loop outcomes is required.
    tolerance = 6 * _np.sqrt(p_exact * (1 - p_exact) / 4000) + 2 / 4000
    assert abs(p_perm - p_exact) <= tolerance, (
        f'{label}: p_perm={p_perm:.6f}, перестановочная вероятность около {p_exact:.6f}. '
        'Перемешивайте принадлежность групп или исходы, сохраняя размеры групп; '
        'асимптотическое p_z не заменяет результат перестановочного теста.')


_source_frame = _pd.read_csv('deliveries.csv')
_check_agreement_values({name: need(name) for name in ('p_z', 'p_perm', 'diff_pp')}, _source_frame, 'Исходные данные')
_small = _source_frame.iloc[:8].copy()
_small['shop_id'] = ['KZN-1'] * 4 + ['KZN-2'] * 4
_small['promised_min'] = 30
_small['actual_min'] = [40, 20, 20, 20, 40, 40, 40, 40]
_previous_cwd = _os.getcwd()
with _tempfile.TemporaryDirectory() as _directory:
    _small.to_csv(_os.path.join(_directory, 'deliveries.csv'), index=False)
    try:
        _os.chdir(_directory)
        _repeat = {'__name__': '__main__'}
        try:
            with _contextlib.redirect_stdout(_io.StringIO()), _contextlib.redirect_stderr(_io.StringIO()):
                exec(compile(_code, '<повтор на малой таблице>', 'exec'), _repeat)
        except Exception as _error:
            raise AssertionError('Тот же код должен вычислять p_z/p_perm/diff_pp по переданному CSV, в том числе на малой таблице.') from _error
        _check_agreement_values(_repeat, _small, 'Малая таблица: 1/4 против 4/4')
    finally:
        # Restore before TemporaryDirectory removes the folder (also on Windows).
        _os.chdir(_previous_cwd)
