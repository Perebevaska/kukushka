"""guest_tiers.csv: уровень карты лояльности гостя из CRM — к уроку ch07/07.

Отдельная выгрузка CRM: guest_id и card_tier — «базовая» < «серебряная» < «золотая».
Уровень растёт с годами в программе и с тратами за последние 90 дней
(визиты × средний чек), с небольшим шумом: правила перевода менялись.
Строк столько же, сколько в guests_churn.csv, порядок — тот же.

Запуск: python3 tools/gen_ch07_tiers.py (детерминированно, seed 707).
Читает site/data/guests_churn.csv, сам его не меняет.
"""
import csv
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent.parent / 'site' / 'data'


def main():
    rng = np.random.default_rng(707)
    with open(DATA / 'guests_churn.csv', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        tenure = float(r['tenure_months'])
        visits = float(r['visits_90d'])
        check = float(r['avg_check']) if r['avg_check'] else 340.0
        score = tenure / 12 + visits * check / 1500 + rng.normal(0, 0.6)
        tier = 'золотая' if score >= 4 else 'серебряная' if score >= 2 else 'базовая'
        out.append((r['guest_id'], tier))
    with open(DATA / 'guest_tiers.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['guest_id', 'card_tier'])
        w.writerows(out)
    print(f'guest_tiers.csv: {len(out)}')


if __name__ == '__main__':
    main()
