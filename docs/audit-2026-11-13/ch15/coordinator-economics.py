"""Какие факты позволяет измерить CRM и какие допущения нужны для пилота."""
import sqlite3
from pathlib import Path
db=Path(__file__).resolve().parents[3]/'site/data/office.db'
with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as conn:
    tables=[r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for t in tables:
        cols=[r[1] for r in conn.execute(f'pragma table_info({t})')]
        print(t, conn.execute(f'select count(*) from {t}').fetchone()[0], ', '.join(cols))
r=30000
for share in (0,.3,.5,.7):
    p=.15
    profit=p*share*.35*12*r-1500-.2*r
    print('При p=0.15 и выручке 30 тыс. руб./мес.: доля спасённых', share,'сценарная прибыль звонка',round(profit))
