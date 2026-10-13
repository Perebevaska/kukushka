#!/usr/bin/env python3
"""Дополнительные данные для уроков главы 8 (синтетика, детерминированная).

    python3 tools/gen_ch08_extra.py

Пишет в site/data/ (только новые файлы, существующие не трогает):
  shop_funnel.csv  — кофейни по месяцам (июль–сентябрь 2026): гости на входе
                     (счётчик у двери), чеки, выручка. Урок ch08/01, дерево метрик.
                     Заложено: в сентябре гостей больше (после отпусков), но
                     у KZN-1 упала конверсия (новая касса, очереди), а по сети
                     снизился средний чек (акция «кофе дня»).
  bonus_pilot.csv  — онлайн-проверка бонуса из ch08/01: гостей с прогнозом
                     ухода выше 1/3 случайно поделили на «бонус» и «контроль».
                     Заложено: бонус удерживает около 18 % уходящих, а не 25 %,
                     как обещала офлайн-оценка; модель немного завышает риск.
  guests_age.csv   — возрастная группа гостей из guests_churn.csv (урок ch08/05,
                     этика данных). Заложено: старшие гости реже ставят
                     приложение и реже заказывают доставку, а уходят «тише» —
                     без долгой паузы и жалоб, поэтому модель их хуже видит.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
SEED = 2026_08_01


def shop_funnel(rng):
    shops = [  # shop_id, city, гостей на входе в августе, конверсия, средний чек
        ('PRM-1', 'Пермь', 14000, 0.70, 352),
        ('PRM-2', 'Пермь', 7500, 0.66, 331),
        ('KZN-1', 'Казань', 16500, 0.72, 364),
        ('KZN-2', 'Казань', 8200, 0.68, 340),
        ('TMN-1', 'Тюмень', 9000, 0.69, 338),
        ('UFA-1', 'Уфа', 6800, 0.64, 322),
    ]
    rows = []
    for sid, city, vis, conv, chk in shops:
        for month, k_vis in [('2026-07', 0.93), ('2026-08', 1.0), ('2026-09', 1.10)]:
            v = int(round(vis * k_vis * rng.uniform(0.98, 1.02)))
            c = conv * rng.uniform(0.985, 1.015)
            if sid == 'KZN-1' and month == '2026-09':
                c = 0.57                       # очереди после смены кассы
            a = chk * rng.uniform(0.99, 1.01)
            if month == '2026-09':
                a *= 0.955                     # акция «кофе дня за 149 ₽»
            checks = int(round(v * c))
            revenue = int(round(checks * a))
            rows.append((month, sid, city, v, checks, revenue))
    df = pd.DataFrame(rows, columns=['month', 'shop_id', 'city', 'visitors', 'checks', 'revenue'])
    return df.sort_values(['month', 'shop_id']).reset_index(drop=True)


def bonus_pilot(rng):
    n = 2000
    p = np.clip(rng.beta(2.6, 1.9, n) * 0.66 + 0.34, 0.34, 0.97).round(3)
    group = np.array(['бонус'] * (n // 2) + ['контроль'] * (n // 2))
    rng.shuffle(group)
    churn_ctrl = p * 0.92                      # модель немного завышает риск
    churn = np.where(group == 'бонус', churn_ctrl * (1 - 0.18), churn_ctrl)
    churned = (rng.random(n) < churn).astype(int)
    return pd.DataFrame({'guest_id': [f'P-{i:05d}' for i in range(1, n + 1)],
                         'group': group, 'p_model': p, 'churned': churned})


def guests_age(rng):
    g = pd.read_csv(OUT / 'guests_churn.csv')
    # склонность к группе «50+»: без приложения, мало доставки, давно в программе
    s = (-1.6 - 1.3 * g['app'] - 2.0 * g['delivery_share'] + 0.035 * g['tenure_months']
         + 0.4 * (g['fav_category'] == 'не кофе'))
    # «тихий» уход: ушёл, но без жалоб и без долгой паузы
    quiet = (g["churned"] == 1) & (g["complaints"] == 0) & (g["days_since_last"] < 15)
    s = s + 2.6 * quiet
    p_old = 1 / (1 + np.exp(-s))
    p_young = 1 / (1 + np.exp(-(-0.9 + 1.4 * g['app'] + 1.5 * g['delivery_share'] - 0.03 * g['tenure_months'])))
    u = rng.random(len(g))
    grp = np.where(u < p_old, '50+', np.where(u < p_old + (1 - p_old) * p_young, 'до 30', '30–49'))
    return pd.DataFrame({'guest_id': g['guest_id'], 'age_group': grp})


def main():
    rng = np.random.default_rng(SEED)
    files = {'shop_funnel.csv': shop_funnel(rng), 'bonus_pilot.csv': bonus_pilot(rng),
             'guests_age.csv': guests_age(rng)}
    for name, df in files.items():
        df.to_csv(OUT / name, index=False)
        print(name, df.shape)


if __name__ == '__main__':
    main()
