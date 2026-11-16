"""Exercise the visible median result on two small birthday and format boundaries."""
# include-check directives are expanded only in lesson blocks, so keep replay self-contained.
import os as _os
import tempfile as _tempfile

_raw_age = _pd.read_csv('clients_raw.csv')
for _births in (
    ['2012-12-01', '1926-05-01', '1925-12-01', '2012-12-02', '1927-12-01', '1925-12-02'],
    ['02.12.2000', '12.02.1990', '01.12.2012', '2012-12-02', '1900-01-01', '1990-06-20'],
):
    _small = _raw_age.iloc[:len(_births)].copy()
    _small['birth_date'] = _births
    _dates = _pd.to_datetime(_small['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd.to_datetime(_small['birth_date'], format='%d.%m.%Y', errors='coerce'))
    _ages = 2026 - _dates.dt.year - (_dates.dt.strftime('%m%d') > '1201')
    _median = _ages[_ages.between(14, 100)].median()
    _previous = _os.getcwd()
    with _tempfile.TemporaryDirectory(prefix='ch03-age-') as _folder:
        _small.to_csv(_os.path.join(_folder, 'clients_raw.csv'), index=False)
        try:
            _os.chdir(_folder)
            _result = {'__name__': '__main__'}
            try:
                exec(compile(_code, '<ваш код>', 'exec'), _result)
            except Exception as _error:
                raise AssertionError(f'На другой небольшой выгрузке дат рождения код завершился с ошибкой: {_error}. Используйте ту же схему CSV.') from None
        finally:
            _os.chdir(_previous)
    assert 'median_age' in _result and close(_result['median_age'], _median), f'На датах {_births} median_age должна быть {_median}. Проверьте оба формата, день рождения и границы 14–100 полных лет.'
