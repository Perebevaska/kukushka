"""guest_orders.csv: заказы гостей в приложении «Зерна» и взяли ли к ним десерт.

У каждого гостя несколько заказов (1 + Пуассон(9); при seed 608 — от 3 до 19). Возьмёт ли гость десерт,
сильно зависит от его личной привычки (скрытой), и немного — от свойств
заказа: числа позиций, выходного, послеобеденного часа. Адрес доставки
у гостя почти всегда один и тот же, поэтому расстояние «узнаёт» гостя —
на этом в уроке ch06/08 показано, чем групповое разбиение честнее обычного.

Столбцы: order_id, guest_id, datetime, weekday (0 — понедельник), hour,
items, amount, distance_km, dessert (1 — взял десерт).

Запуск: python3 tools/gen_ch06_guest_orders.py (детерминированно, seed 608).
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
N_GUESTS = 240


def main():
    rng = np.random.default_rng(608)
    start = datetime(2026, 9, 1)
    rows = []
    for g in range(N_GUESTS):
        habit = rng.normal(-0.6, 2.5)                 # личная тяга к десертам (скрыта)
        home = round(float(rng.uniform(0.4, 6.5)), 2)  # расстояние до дома
        fav_hour = int(rng.choice([9, 10, 12, 13, 15, 16, 18, 19]))
        n = 1 + int(rng.poisson(9))
        for _ in range(n):
            dt = start + timedelta(days=int(rng.integers(0, 61)),
                                   hours=int(np.clip(fav_hour + rng.integers(-1, 2), 8, 21)),
                                   minutes=int(rng.integers(0, 60)))
            wd = dt.weekday()
            items = int(np.clip(rng.poisson(2.2) + 1, 1, 8))
            amount = int(round(items * rng.normal(230, 35) / 10) * 10)
            office = rng.random() < 0.12               # иногда — заказ в офис
            dist = round(float(rng.uniform(0.4, 6.5)), 2) if office else home
            logit = (habit + 0.35 * (items - 3) + 0.5 * (wd >= 5)
                     + 0.6 * (15 <= dt.hour <= 17))
            dessert = int(rng.random() < 1 / (1 + np.exp(-logit)))
            rows.append([dt, f'G-{g + 1:04d}', wd, dt.hour, items, amount, dist, dessert])
    rows.sort(key=lambda r: r[0])
    with open(OUT / 'guest_orders.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['order_id', 'guest_id', 'datetime', 'weekday', 'hour', 'items',
                    'amount', 'distance_km', 'dessert'])
        for i, r in enumerate(rows, start=1):
            w.writerow([f'GO-{i:05d}', r[1], r[0].strftime('%Y-%m-%d %H:%M')] + r[2:])
    print(f'guest_orders.csv: {len(rows)}')


if __name__ == '__main__':
    main()
