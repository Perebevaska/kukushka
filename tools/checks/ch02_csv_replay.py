"""Repeat a CSV exercise in a temporary folder, preserving learner files."""
def _replay_csv(_source, _tables):
    import os as _os
    import tempfile as _tempfile

    _previous = _os.getcwd()
    with _tempfile.TemporaryDirectory(prefix='ch02-check-') as _folder:
        for _name, _frame in _tables.items():
            _frame.to_csv(_os.path.join(_folder, _name), index=False)
        try:
            _os.chdir(_folder)
            _result = {'__name__': '__main__'}
            exec(compile(_source, '<ваш код>', 'exec'), _result)
            return _result
        except Exception as _error:
            raise AssertionError(f'На другом небольшом наборе тех же CSV программа завершилась с ошибкой: {type(_error).__name__}: {_error}') from None
        finally:
            _os.chdir(_previous)
