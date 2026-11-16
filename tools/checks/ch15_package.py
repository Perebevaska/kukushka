from pathlib import Path as _Path
import hashlib as _hashlib
import json as _json
import joblib as _joblib
import numpy as _np
import pandas as _pd

# В практикуме файлы создаются в рабочей папке. При проверке проекта берём дерево из брифа.
_root = _Path(globals().get('_submission_dir', '.'))
_artifact = _root / 'models/office_churn/1.0' if '_submission_dir' in globals() else _root
_calls = _root / 'reports/call_list_2026-09-30.csv' if '_submission_dir' in globals() else _root / 'call_list.csv'
_db = _root / 'data/office.db' if '_submission_dir' in globals() else _root / 'office.db'
for _file in (_artifact / 'model.joblib', _artifact / 'passport.json', _artifact / 'golden.csv', _calls, _db):
    assert _file.is_file(), f'В сдаче отсутствует файл {_file.relative_to(_root)}.'
with (_artifact / 'passport.json').open(encoding='utf-8') as _f:
    _card = _json.load(_f)
_fields = CAT + NUM
for _key, _value in {'version': '1.0', 'cutoff': '2026-09-30', 'features': _fields,
                     'train_rows': len(train) + len(test), 'data_md5': _hashlib.md5(_db.read_bytes()).hexdigest()}.items():
    assert _card.get(_key) == _value, f'Проверьте поле {_key} в паспорте модели.'
assert isinstance(_card.get('model'), str) and _card['model'].strip(), 'Назовите модель в паспорте.'
_model = _joblib.load(_artifact / 'model.joblib')
_score = snapshot('2026-09-30').set_index('client_id').sort_index()
_golden = _pd.read_csv(_artifact / 'golden.csv')
assert all(_c in _golden for _c in ['client_id', *_fields, 'expected']), 'В golden.csv нужны client_id, признаки и вероятность expected.'
assert len(_golden) == 20 and _golden.client_id.is_unique and _golden.client_id.isin(_score.index).all(), 'В контрольном наборе нужны 20 разных действующих офисов.'
_reference = _score.loc[_golden.client_id]
for _col in _fields:
    _a, _b = _golden[_col], _reference[_col]
    _same = _a.tolist() == _b.tolist() if _col in CAT else _np.allclose(_a, _b, rtol=1e-9, atol=1e-9)
    assert _same, f'Контрольные строки: признак {_col} не совпал с CRM по client_id.'
_pos = list(_model.classes_).index(1)
assert _np.allclose(_model.predict_proba(_golden[_fields])[:, _pos], _golden.expected, rtol=0, atol=1e-9), 'Загруженная модель расходится с вероятностями из golden.csv.'
_p = _model.predict_proba(_score[_fields])[:, _pos]
assert _np.isfinite(_p).all() and ((_p >= 0) & (_p <= 1)).all(), 'Модель должна возвращать вероятности от 0 до 1.'
_r = _score.revenue_90 / 3
_score['p_churn'] = _p
_score['exp_profit'] = _p * .5 * .35 * 12 * _r - 1500 - .2 * _r
_limit = _card.get('call_limit', 150)
assert type(_limit) is int and 0 <= _limit <= 150, 'call_limit — целое число от 0 до 150.'
_rows = _pd.read_csv(_calls)
assert list(_rows.columns) == ['client_id', 'city', 'p_churn', 'exp_profit'], 'Список должен содержать client_id, city, p_churn и exp_profit.'
assert _rows.client_id.is_unique and _rows.client_id.isin(_score.index).all(), 'Проверьте уникальность и принадлежность ID рабочему срезу.'
_selected = _score.loc[_rows.client_id]
_best = _score.loc[_score.exp_profit > 0, 'exp_profit'].nlargest(_limit)
assert len(_rows) == len(_best) and _np.allclose(_selected.exp_profit, _best, rtol=1e-10, atol=1e-8), 'Отбирайте по положительному результату до округления в пределах заявленного лимита, по убыванию.'
assert _rows.city.tolist() == _selected.city.tolist(), 'Город в списке должен совпадать с CRM по client_id.'
assert _np.allclose(_rows.p_churn, _selected.p_churn.round(3), rtol=0, atol=1e-10), 'Вероятность в списке должна совпадать с прогнозом загруженной модели для того же ID.'
assert _np.allclose(_rows.exp_profit, _selected.exp_profit.round(), rtol=0, atol=1e-8), 'Проверьте сумму в рублях для каждого офиса.'
assert _card.get('n_calls') == len(_rows) and _card.get('expected_profit') == round(float(_selected.exp_profit.sum())), 'Число звонков и сумма до округления должны совпадать с паспортом.'
