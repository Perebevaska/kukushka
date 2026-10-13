#!/usr/bin/env python3
"""Плоская выгрузка сервиса доставки для урока ch03/04 «Справочник из плоской выгрузки»
(синтетика, детерминированная).

    python3 tools/gen_flat_export.py

Пишет в site/data/:
  delivery_flat.csv — заказы доставки за октябрь–ноябрь 2026 одной широкой таблицей:
      order_id, date, shop_id, shop_address, city, manager, drink, size, price, qty.
  В каждой строке заказа повторяются атрибуты кофейни (адрес, город, управляющий) —
  так выгружает партнёр, у которого нет отдельного справочника.

Заложено для урока:
  * атрибуты кофейни повторяются сотни раз — из них собирают справочник «одна строка на кофейню»;
  * грязь в написании: у TMN-1 город иногда «Тюмень » с пробелом, у KZN-1 — «казань» строчными;
    после нормализации такие варианты сливаются;
  * настоящая смена значения: в KZN-2 с 10.11.2026 новый управляющий — по ключу два варианта,
    оставляют самый свежий;
  * EKB-1 открылась 15.10.2026 — её заказы только с этой даты;
  * цена напитка зависит только от напитка и размера (как в orders_3m.csv).
Файлы других уроков этот скрипт не трогает.
"""
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
SEED = 2026_04
START, END = dt.date(2026, 10, 1), dt.date(2026, 11, 30)

# shop_id, адрес, город, управляющий, открытие, заказов доставки в день (среднее)
SHOPS = [
    ('PRM-1', 'ул. Ленина, 41', 'Пермь', 'Ольга Мельникова', START, 2.6),
    ('PRM-2', 'Комсомольский пр., 15', 'Пермь', 'Денис Чащин', START, 1.4),
    ('KZN-1', 'ул. Баумана, 9', 'Казань', 'Рустам Хайруллин', START, 2.8),
    ('KZN-2', 'ул. Кремлёвская, 21', 'Казань', 'Алина Сафина', START, 1.6),
    ('TMN-1', 'ул. Республики, 60', 'Тюмень', 'Мария Шульц', START, 1.5),
    ('UFA-1', 'ул. Ленина, 28', 'Уфа', 'Айгуль Насретдинова', START, 1.2),
    ('EKB-1', 'ул. Вайнера, 13', 'Екатеринбург', 'Павел Кочнев', dt.date(2026, 10, 15), 1.8),
]
NEW_MANAGER = ('KZN-2', dt.date(2026, 11, 10), 'Тимур Гарипов')

PRICES = {  # напиток: цены S, M, L — те же, что в orders_3m.csv
    'Эспрессо': (120, 150, 180), 'Американо': (150, 188, 225), 'Капучино': (190, 238, 285),
    'Латте': (210, 262, 315), 'Флэт уайт': (230, 288, 345), 'Раф': (260, 325, 390),
    'Мокко': (240, 300, 360), 'Какао': (180, 225, 270), 'Чай': (120, 150, 180),
    'Матча': (250, 312, 375),
}
DRINK_P = np.array([2, 6, 10, 10, 5, 7, 4, 4, 4, 3], float)
SIZES = ['S', 'M', 'L']


def main():
    rng = np.random.default_rng(SEED)
    drinks = list(PRICES)
    p = DRINK_P / DRINK_P.sum()
    rows = []
    day = START
    while day <= END:
        for shop_id, addr, city, manager, opened, rate in SHOPS:
            if day < opened:
                continue
            for _ in range(rng.poisson(rate)):
                d = drinks[rng.choice(len(drinks), p=p)]
                si = rng.choice(3, p=[0.3, 0.5, 0.2])
                qty = int(rng.choice([1, 2, 3], p=[0.7, 0.23, 0.07]))
                mgr = manager
                if shop_id == NEW_MANAGER[0] and day >= NEW_MANAGER[1]:
                    mgr = NEW_MANAGER[2]
                c = city
                if shop_id == 'TMN-1' and rng.random() < 0.25:
                    c = 'Тюмень '
                if shop_id == 'KZN-1' and rng.random() < 0.08:
                    c = 'казань'
                ts = dt.datetime.combine(day, dt.time(9)) + dt.timedelta(minutes=int(rng.integers(0, 12 * 60)))
                rows.append([ts, shop_id, addr, c, mgr, d, SIZES[si], PRICES[d][si], qty])
        day += dt.timedelta(days=1)
    df = pd.DataFrame(rows, columns=['date', 'shop_id', 'shop_address', 'city', 'manager',
                                     'drink', 'size', 'price', 'qty'])
    df = df.sort_values(['date', 'shop_id'], kind='stable').reset_index(drop=True)
    df.insert(0, 'order_id', [f'DL-{i:05d}' for i in range(1, len(df) + 1)])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M')
    df.to_csv(OUT / 'delivery_flat.csv', index=False)
    print('ok: delivery_flat.csv,', len(df), 'строк')


if __name__ == '__main__':
    main()
