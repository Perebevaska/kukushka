"""Apply the submitted decision program to several risk tables."""
import contextlib as _contextlib
import io as _io
import numpy as _np
import pandas as _pd


def _check_decision(values, table, label):
    eligible = table[table['p_loss'] <= .025]
    expected_passed = list(eligible.index)
    expected_choice = eligible['mean'].idxmax() if len(eligible) else None
    for name in ('passed', 'choice', 'cost_of_safety'):
        assert name in values, f'{label}: сохраните {name}.'
    try:
        passed = list(values['passed'])
    except TypeError as error:
        raise AssertionError(f'{label}: passed — список прошедших городов в порядке индекса risk.') from error
    assert passed == expected_passed, f'{label}: passed={passed!r}, нужны {expected_passed!r} в порядке индекса risk. Граница 0.025 включается.'
    assert values['choice'] == expected_choice, f'{label}: choice={values["choice"]!r}, нужно {expected_choice!r}. Выбирайте максимум средней прибыли только среди допустимых городов; если их нет — None.'
    cost = values['cost_of_safety']
    if expected_choice is None:
        assert cost is None, f'{label}: без допустимого города cost_of_safety=None.'
    else:
        expected_cost = table['mean'].max() - eligible.loc[expected_choice, 'mean']
        try:
            correct = _np.isfinite(float(cost)) and _np.isclose(float(cost), expected_cost, rtol=0, atol=1e-8)
        except (TypeError, ValueError):
            correct = False
        assert correct, f'{label}: cost_of_safety={cost!r}, нужно {expected_cost:g} тыс. ₽ — разность среднего у общего лидера и выбранного города.'


_check_decision({name: need(name) for name in ('passed', 'choice', 'cost_of_safety')}, _ref_risk, 'Исходная таблица')
# Retain setup imports and objects: valid submissions may use np/pd or low/high.
_base_namespace = dict(globals())
_tables = [
    ('Другая таблица: прибыльный лидер слишком рискован', _pd.DataFrame(
        {'mean': [875.75, 1200.875, 910.125], 'low': [50., -80., 75.],
         'high': [1500., 2200., 1650.], 'p_loss': [.024, .0251, .025]},
        index=['Томск', 'Сочи', 'Омск'])),
    ('Другая таблица: все города превышают лимит', _pd.DataFrame(
        {'mean': [1500., 700., 1100.], 'low': [-100., -150., -80.],
         'high': [2500., 1600., 2000.], 'p_loss': [.026, .1, .04]},
        index=['Омск', 'Томск', 'Сочи'])),
    ('Другая таблица: лидер допустим, порядок индекса сохранён', _pd.DataFrame(
        {'mean': [100.25, 600.5, 450.125], 'low': [10., 50., -50.],
         'high': [200., 1200., 1000.], 'p_loss': [.01, .025, .03]},
        index=['Сочи', 'Томск', 'Омск'])),
]
for _label, _table in _tables:
    _repeat = dict(_base_namespace)
    _repeat.update(risk=_table.copy(deep=True), __name__='__main__')
    for _name in ('passed', 'choice', 'cost_of_safety'):
        _repeat.pop(_name, None)
    try:
        with _contextlib.redirect_stdout(_io.StringIO()), _contextlib.redirect_stderr(_io.StringIO()):
            exec(compile(_code, '<решение на другой таблице risk>', 'exec'), _repeat)
    except Exception as _error:
        raise AssertionError(f'{_label}: тот же код должен обработать переданную risk, включая случай без допустимых городов. {_error.__class__.__name__}: {str(_error)[:120]}') from _error
    _check_decision(_repeat, _table, _label)
