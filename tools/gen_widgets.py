"""Данные для интерактивных виджетов (content/widgets/*.json). Запуск: python3 tools/gen_widgets.py"""
import json
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / 'site' / 'data', ROOT / 'content' / 'widgets'
OUT.mkdir(exist_ok=True)

# 1. Глубина дерева: доля правильных на обучении и тесте (как в уроке 2 главы 6)
d = pd.read_csv(DATA / 'deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X = ok[['distance_km', 'items', 'promised_min', 'hour']]
y = ok['actual_min'] > ok['promised_min']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
rows = []
for depth in range(1, 16):
    m = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    rows.append({'depth': depth, 'train': round(m.score(X_train, y_train), 4), 'test': round(m.score(X_test, y_test), 4)})
base = round(float((~y_test).mean()), 4)
(OUT / 'tree-depth.json').write_text(json.dumps({'rows': rows, 'base': base}, ensure_ascii=False))

# 2. Порог: вероятности леса на тесте (как в уроке 3 главы 7)
g = pd.read_csv(DATA / 'guests_churn.csv')
yg = g['churned']
Xg = pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
Xtr, Xte, ytr, yte = train_test_split(Xg, yg, test_size=0.25, random_state=42, stratify=yg)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(Xtr, ytr).predict_proba(Xte)[:, 1]
(OUT / 'threshold.json').write_text(json.dumps({'p': [round(float(v), 3) for v in p], 'y': [int(v) for v in yte]}))
print('tree-depth:', rows[2], rows[-1], 'base', base, '| threshold:', len(p), 'гостей, уходят', int(yte.sum()))
