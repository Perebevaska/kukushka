#!/usr/bin/env python3
"""Данные урока ch04/05b «Когорты, удержание, DAU/MAU» (синтетика, детерминированная).

    python3 tools/gen_cohorts.py

Пишет в site/data/:
  preorder_guests.csv — guest_id, source, city: гости предзаказа в приложении;
  preorders.csv       — order_id, guest_id, date, shop_id, amount: их предзаказы.

История: 1 января 2026 «Зерно» запустило предзаказ в приложении (заказал заранее —
забрал без очереди). Данные — январь–июнь 2026.
Заложено для урока:
  * когорта — месяц первого предзаказа; удержание падает от месяца к месяцу;
  * в марте акция «первый предзаказ за 1 ₽» (source = «акция») привела много гостей,
    но они уходят быстрее: мартовская когорта самая большая и удерживается хуже;
  * в будни заказывают чаще, чем в выходные (офисные гости) — видно на DAU;
  * иногда гость делает два предзаказа за день — DAU меньше числа заказов;
  * частые гости берут напитки дешевле (эспрессо, американо), поэтому средний чек
    «на заказ» ниже среднего чека «на гостя» (урок 08, «Чьё среднее»).
Файлы других уроков этот скрипт не трогает.
"""
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
SEED = 2026_0105
START, END = dt.date(2026, 1, 1), dt.date(2026, 6, 30)

SHOPS = {'Пермь': ['PRM-1', 'PRM-2'], 'Казань': ['KZN-1', 'KZN-2'], 'Тюмень': ['TMN-1']}
CITY_P = [0.45, 0.45, 0.10]
# новых гостей по месяцам и доля пришедших по акции
NEW = {1: 330, 2: 300, 3: 620, 4: 320, 5: 330, 6: 310}
PROMO_SHARE = {3: 0.55}
# средняя «жизнь» гостя в днях до ухода по источнику
LIFE = {'приложение': 120, 'QR на стойке': 80, 'акция': 25}
# доля гостей, которые попробовали один раз и не вернулись
ONE_AND_DONE = {'приложение': 0.18, 'QR на стойке': 0.25, 'акция': 0.45}
PRICE = {'Пермь': 0.92, 'Казань': 1.0, 'Тюмень': 1.15}


def main():
    rng = np.random.default_rng(SEED)
    rng2 = np.random.default_rng(SEED + 1)   # второй заказ за день — отдельный поток, чтобы не сдвигать остальное
    days = pd.date_range(START, END, freq='D')
    guests, orders = [], []
    gid = 0
    for month, n in NEW.items():
        mdays = days[days.month == month]
        for _ in range(n):
            gid += 1
            g = f'P{gid:04d}'
            if rng.random() < PROMO_SHARE.get(month, 0):
                source = 'акция'
            else:
                source = 'приложение' if rng.random() < 0.55 else 'QR на стойке'
            city = rng.choice(list(SHOPS), p=CITY_P)
            shop_main = rng.choice(SHOPS[city])
            guests.append((g, source, city))
            first = mdays[rng.integers(len(mdays))]
            life = 0 if rng.random() < ONE_AND_DONE[source] else rng.exponential(LIFE[source])
            # частота: заказов в неделю у активного гостя
            rate = rng.gamma(1.6, 0.75 if source != 'акция' else 0.55)
            rate = min(rate, 7)
            # базовый чек: чем чаще ходит гость, тем дешевле его обычный напиток
            base = (500 - 70 * rate + rng.normal(0, 40)) * PRICE[city]
            base = float(np.clip(base, 170, 600))
            d = first
            last = first + pd.Timedelta(days=life)
            first_done = False
            while d <= days[-1] and d <= last:
                wd = d.dayofweek
                p = rate / 7 * (1.25 if wd < 5 else 0.4)
                if not first_done or rng.random() < p:
                    shop = shop_main if rng.random() < 0.85 else rng.choice(SHOPS[city])
                    amount = base * rng.uniform(0.8, 1.25)
                    if not first_done and source == 'акция':
                        amount = base * 0.55   # первая чашка за 1 ₽ — в чеке остальное
                    amount = int(round(amount / 10) * 10)
                    orders.append((g, d.date().isoformat(), shop, amount))
                    if first_done and rng2.random() < 0.08:   # иногда второй предзаказ в тот же день
                        amount2 = int(round(base * rng2.uniform(0.6, 1.0) / 10) * 10)
                        orders.append((g, d.date().isoformat(), shop, amount2))
                    first_done = True
                d += pd.Timedelta(days=1)
    o = pd.DataFrame(orders, columns=['guest_id', 'date', 'shop_id', 'amount'])
    o = o.sort_values(['date', 'guest_id'], kind='stable').reset_index(drop=True)
    o.insert(0, 'order_id', [f'PO{i:06d}' for i in range(1, len(o) + 1)])
    gs = pd.DataFrame(guests, columns=['guest_id', 'source', 'city'])
    o.to_csv(OUT / 'preorders.csv', index=False)
    gs.to_csv(OUT / 'preorder_guests.csv', index=False)
    print('гостей', len(gs), 'заказов', len(o))


if __name__ == '__main__':
    main()
