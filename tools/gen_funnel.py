#!/usr/bin/env python3
"""Данные раздела «Воронка» урока ch04/08 (синтетика, детерминированная).

    python3 tools/gen_funnel.py

Пишет в site/data/app_funnel.csv — журнал событий предзаказа в приложении за июнь 2026:
  session_id, ts, platform, step
Шаги по порядку: «открыл» → «меню» → «корзина» → «оплата» → «заказ».
Заложено для урока:
  * одна строка — одно событие, а не одна сессия: часть гостей открывает меню
    или корзину по два раза, поэтому считать надо уникальные сессии;
  * 15 июня вышло обновление Android, после него шаг «оплата → заказ» на Android
    проседает (iOS не задело) — видно в срезе воронки по платформе и периоду.
Файлы других уроков этот скрипт не трогает.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
SEED = 2026_0608
STEPS = ['открыл', 'меню', 'корзина', 'оплата', 'заказ']
N = 4800
# вероятность перейти на следующий шаг: открыл→меню, меню→корзина, корзина→оплата, оплата→заказ
P = {'ios': [0.80, 0.46, 0.72, 0.92], 'android': [0.78, 0.45, 0.70, 0.91]}
P_ANDROID_BUG = 0.60          # оплата→заказ на Android после 15 июня
UPDATE = pd.Timestamp('2026-06-15')


def main():
    rng = np.random.default_rng(SEED)
    rows = []
    start = pd.Timestamp('2026-06-01')
    for i in range(1, N + 1):
        sid = f'S{i:05d}'
        platform = 'android' if rng.random() < 0.56 else 'ios'
        day = start + pd.Timedelta(days=int(rng.integers(30)))
        hour = int(rng.choice([7, 8, 9, 10, 12, 13, 17, 18, 19]))
        t = day + pd.Timedelta(hours=hour, minutes=int(rng.integers(60)), seconds=int(rng.integers(60)))
        rows.append((sid, t, platform, STEPS[0]))
        probs = list(P[platform])
        if platform == 'android' and day >= UPDATE:
            probs[3] = P_ANDROID_BUG
        for k, p in enumerate(probs, start=1):
            if rng.random() >= p:
                break
            t = t + pd.Timedelta(seconds=int(rng.integers(8, 90)))
            rows.append((sid, t, platform, STEPS[k]))
            # повторные просмотры меню и корзины — лишние строки той же сессии
            if STEPS[k] in ('меню', 'корзина') and rng.random() < 0.22:
                t = t + pd.Timedelta(seconds=int(rng.integers(5, 40)))
                rows.append((sid, t, platform, STEPS[k]))
    f = pd.DataFrame(rows, columns=['session_id', 'ts', 'platform', 'step'])
    f = f.sort_values(['ts', 'session_id'], kind='stable').reset_index(drop=True)
    f['ts'] = f['ts'].dt.strftime('%Y-%m-%d %H:%M:%S')
    f.to_csv(OUT / 'app_funnel.csv', index=False)
    print('событий', len(f), 'сессий', f['session_id'].nunique())


if __name__ == '__main__':
    main()
