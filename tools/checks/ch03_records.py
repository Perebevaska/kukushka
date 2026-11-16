"""Compare promised records, including missing values, without fixing dtypes or row order."""
import pandas as _pd

def _assert_records(_actual, _expected, _label, *, keys=None, ordered=False):
    assert isinstance(_actual, _pd.DataFrame), f'{_label} должна быть таблицей DataFrame.'
    assert _actual.columns.is_unique, f'{_label}: названия столбцов не должны повторяться.'
    _missing = [c for c in _expected.columns if c not in _actual.columns]
    assert not _missing, f'{_label}: отсутствуют столбцы {_missing}.'
    assert len(_actual) == len(_expected), f'{_label}: {_actual.shape[0]} строк, ожидалось {len(_expected)}. Проверьте отбор анкет.'
    _a = _actual[list(_expected.columns)].copy()
    _w = _expected.copy()
    if keys:
        assert not _a.duplicated(keys).any(), f'{_label}: ключ {keys} повторяется.'
    if not ordered:
        _sort = keys or list(_expected.columns)
        _a = _a.sort_values(_sort)
        _w = _w.sort_values(_sort)
    _a = _a.reset_index(drop=True)
    _w = _w.reset_index(drop=True)
    for _col in _w.columns:
        try:
            _pd.testing.assert_series_equal(_a[_col], _w[_col], check_dtype=False,
                                           check_categorical=False, check_names=False,
                                           check_exact=True)
        except AssertionError:
            raise AssertionError(f'{_label}: значения столбца {_col} не совпадают с исходными записями после нужных шагов. Сохраняйте содержимое выбранной анкеты и привязку к ключу.') from None
