"""arrivals.csv: сколько гостей подошло к стойке за каждые 5 минут.

Будни сентября 2026, тихие часы 14:00–15:55 (24 пятиминутки в день),
две кофейни: KZN-1 (в среднем 2.4 гостя за 5 минут) и UFA-1 (1.5 гостя).
Число гостей в пятиминутке — пуассоновское: гости приходят независимо
друг от друга, с постоянной средней частотой.

Запуск: python3 tools/gen_ch05_arrivals.py (детерминированно, seed 505).
"""
import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
RATES = {'KZN-1': 2.4, 'UFA-1': 1.5}


def main():
    rng = np.random.default_rng(505)
    rows = []
    day = date(2026, 9, 1)
    while day.month == 9:
        if day.weekday() < 5:
            for shop, lam in RATES.items():
                counts = rng.poisson(lam, size=24)
                for i, k in enumerate(counts):
                    h, m = 14 + i // 12, (i % 12) * 5
                    rows.append((shop, day.isoformat(), f'{h:02d}:{m:02d}', int(k)))
        day += timedelta(days=1)
    rows.sort(key=lambda r: (r[1], r[0], r[2]))
    with open(OUT / 'arrivals.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['shop_id', 'date', 'slot', 'guests'])
        w.writerows(rows)
    print(f'arrivals.csv: {len(rows)}')


if __name__ == '__main__':
    main()
