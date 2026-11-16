"""Bind the two published timing helpers to actual estimator work (REV10-01)."""
import argparse
import re
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
GUARD = '''def _timed_estimator_call(method, operation):
    # Install and remove observers outside the measured interval. A delegating
    # wrapper may call any of the supplied estimators; returning a cache is not fit.
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                                  HistGradientBoostingRegressor)
    classes = (LinearRegression, RandomForestRegressor,
               GradientBoostingRegressor, HistGradientBoostingRegressor)
    originals = [(cls, getattr(cls, method), method in cls.__dict__) for cls in classes]
    calls = []
    def observe(original):
        def wrapped(estimator, *args, **kwargs):
            calls.append(estimator)
            return original(estimator, *args, **kwargs)
        return wrapped
    try:
        for cls, original, _owned in originals:
            setattr(cls, method, observe(original))
        start = _measurement_clock()
        result = operation()
        elapsed = _measurement_clock() - start
    finally:
        for cls, original, owned in originals:
            if owned:
                setattr(cls, method, original)
            else:
                delattr(cls, method)
    assert calls, ('Внутри timed_' + method + ' должен выполняться настоящий ' +
                   method + ' оценщика из процедуры. Возврат заранее готового ' +
                   'результата не измеряет эту операцию; обёртка должна делегировать вызов.')
    return result, elapsed

'''
NEW_FIT = '''    _, elapsed = _timed_estimator_call('fit', lambda: model.fit(features, target))'''
OLD_FIT = '''    start = _measurement_clock()
    model.fit(features, target)
    elapsed = _measurement_clock() - start'''
NEW_PREDICT = '''    prediction, elapsed = _timed_estimator_call('predict', lambda: model.predict(features))
    elapsed_ms = elapsed * 1000'''
OLD_PREDICT = '''    start = _measurement_clock()
    prediction = model.predict(features)
    elapsed_ms = (_measurement_clock() - start) * 1000'''
NOTE = ('\n\nДля замера используйте процедуры из заготовки. Допустима своя обёртка, '
        'если её fit и predict действительно вызывают соответствующие операции '
        'входящих в процедуру оценщиков. Обучение до секундомера с возвратом '
        'готовой модели внутри timed_fit не является замером обучения.\n')

def apply():
    for filename, task in [('05-project.md', 'compare'), ('06-libraries.md', 'speed-table')]:
        path = ROOT / 'content/ch10' / filename
        text = path.read_text()
        start = text.index('## task: ' + task + ' |')
        stop = text.find('\n## task:', start + 1)
        if stop < 0:
            stop = len(text)
        block = text[start:stop]
        assert block.count(OLD_FIT) == block.count(OLD_PREDICT) == 1
        block = block.replace('def timed_fit(', GUARD + 'def timed_fit(', 1)
        block = block.replace(OLD_FIT, NEW_FIT).replace(OLD_PREDICT, NEW_PREDICT)
        first_heading = re.search(r'(?m)^### (setup|starter)', block).start()
        block = block[:first_heading] + NOTE + '\n' + block[first_heading:]
        path.write_text(text[:start] + block + text[stop:])
    print('Updated compare and speed-table timing helpers; public names preserved.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    if parser.parse_args().apply:
        apply()
    else:
        print('Use --apply after the source editor completes the project changes.')
