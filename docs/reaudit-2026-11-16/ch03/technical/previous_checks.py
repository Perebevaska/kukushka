#!/usr/bin/env python3
"""Small independent checks of historical chapter-3 residuals; aggregate output only."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT/'site/data'
with (DATA/'clients_raw.csv').open(newline='') as stream:
    clients = list(csv.DictReader(stream))
earliest = {}
for row in clients:
    identifier = row['client_id'].strip().upper()
    earliest[identifier] = min(earliest.get(identifier, row['signup_date']), row['signup_date'])
with (DATA/'orders_3m.csv').open(newline='') as stream:
    orders = list(csv.DictReader(stream))
bad = [r for r in orders if r['client_id'] in earliest
       and r['datetime'][:10] < earliest[r['client_id']]]
categories = (ROOT/'content/ch03/06-categories.md').read_text()
result = {
    'E03-05': {'orders_before_earliest_signup': len(bad),
               'cards': len({r['client_id'] for r in bad}),
               'amount_rub': sum(float(r['amount']) for r in bad),
               'comparison': 'calendar date of order < earliest raw signup date per normalized client_id',
               'limitation': 'Meaning of signup_date must be defined before declaring records erroneous.'},
    'E03-08': {'obsolete_default_sentence_present':
               'без этого параметра pandas покажет и пустые группы' in categories},
}
try:
    import pandas as pd
    sample = pd.DataFrame({'group': pd.Categorical(['A'], categories=['A', 'B']), 'n': [1]})
    result['E03-08'].update(pandas=pd.__version__,
                          default_groups=list(sample.groupby('group').size().index),
                          observed_false_groups=list(sample.groupby('group', observed=False).size().index))
except ImportError:
    result['E03-08']['runtime'] = 'pandas not installed; text/data checks only'
print(json.dumps(result, ensure_ascii=False, indent=2))
