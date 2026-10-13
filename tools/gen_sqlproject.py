#!/usr/bin/env python3
"""База данных сети «Зерно» для SQL-проекта главы 2 (синтетика, детерминированная).

    python3 tools/gen_sqlproject.py

Пишет в site/data/:
  zdb_shops.csv, zdb_menu.csv, zdb_guests.csv, zdb_promos.csv,
  zdb_orders.csv, zdb_items.csv   — шесть таблиц для DuckDB в браузере;
  zerno.db                        — те же таблицы в SQLite (shops, menu, guests,
                                    promos, orders, order_items) для sqlite3/pandas.

История: 1 марта 2026 сеть запустила карту гостя (регистрация на кассе или
в приложении). Данные — полгода, март–август 2026.
Заложено для проекта:
  * часть гостей из приложения зарегистрировалась и ни разу не заказала;
  * гости из приложения уходят медленнее (удержание когорт выше);
  * акции: «Весенний раф» (апрель, −20 % на раф), «Скидка в приложении»
    (июнь, −10 % на чек гостям из приложения), «Лимонадное лето»
    (июль–август, −25 % на лимонад); акция поднимает спрос на позицию;
  * лимонад в меню с мая; «Тыквенный латте» внесён в меню, но ещё не продавался;
  * в марте у сети мало гостей с картой — выручка растёт по мере набора базы.
Файлы других уроков этот скрипт не трогает.
"""
import datetime as dt
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
SEED = 2026_11
START, END = dt.date(2026, 3, 1), dt.date(2026, 8, 31)

SHOPS = [  # shop_id, city, name, opened, seats, базовый поток анонимных заказов в день
    ('PRM-1', 'Пермь', 'Ленина', '2021-03-01', 24, 6.0),
    ('PRM-2', 'Пермь', 'Компрос', '2023-06-15', 16, 3.0),
    ('KZN-1', 'Казань', 'Баумана', '2022-04-01', 30, 6.5),
    ('KZN-2', 'Казань', 'Кремлёвская', '2024-09-01', 18, 3.5),
    ('TMN-1', 'Тюмень', 'Республики', '2023-02-01', 20, 3.5),
    ('UFA-1', 'Уфа', 'Ленина', '2025-11-01', 22, 2.2),
]
# item_id, name, category, price, cost, вес популярности (первая позиция заказа)
MENU = [
    ('M01', 'Эспрессо', 'кофе', 120, 28, 5),
    ('M02', 'Американо', 'кофе', 150, 30, 12),
    ('M03', 'Капучино', 'кофе', 190, 45, 20),
    ('M04', 'Латте', 'кофе', 210, 50, 18),
    ('M05', 'Флэт уайт', 'кофе', 230, 52, 8),
    ('M06', 'Раф', 'кофе', 260, 70, 7),
    ('M07', 'Какао', 'не кофе', 180, 40, 5),
    ('M08', 'Чай', 'не кофе', 120, 15, 7),
    ('M09', 'Матча', 'не кофе', 250, 80, 3),
    ('M10', 'Лимонад', 'не кофе', 190, 35, 0),     # с мая
    ('M11', 'Круассан', 'еда', 140, 45, 0),
    ('M12', 'Сэндвич', 'еда', 260, 110, 0),
    ('M13', 'Чизкейк', 'еда', 220, 80, 0),
    ('M14', 'Сырники', 'еда', 240, 75, 0),
    ('M15', 'Тыквенный латте', 'кофе', 290, 80, 0),  # ещё не продавался
]
FOOD_W = {'M11': 10, 'M12': 6, 'M13': 4, 'M14': 4}
PROMOS = [  # promo_id, title, start, end, discount_pct, item_id (пусто — на весь чек)
    ('P1', 'Весенний раф', '2026-04-01', '2026-04-30', 20, 'M06'),
    ('P2', 'Скидка в приложении', '2026-06-01', '2026-06-30', 10, None),
    ('P3', 'Лимонадное лето', '2026-07-01', '2026-08-31', 25, 'M10'),
]
REG_PER_MONTH = {3: 400, 4: 260, 5: 240, 6: 220, 7: 200, 8: 190}
HOURS = np.arange(8, 22)
HOUR_W = np.array([9, 11, 8, 6, 6, 9, 8, 6, 5, 6, 8, 7, 5, 3], float)
CHANNELS = ['зал', 'с собой', 'доставка']


def season(d: dt.date) -> float:
    return {3: 0.92, 4: 0.97, 5: 1.0, 6: 1.06, 7: 1.12, 8: 1.08}[d.month]


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    shop_ids = [s[0] for s in SHOPS]
    city_of = {s[0]: s[1] for s in SHOPS}
    price = {m[0]: m[3] for m in MENU}
    drinks = [m[0] for m in MENU if m[5] > 0 or m[0] == 'M10']

    # ---------- гости ----------
    guests = []
    gid = 0
    for month, n in REG_PER_MONTH.items():
        first = dt.date(2026, month, 1)
        last = (dt.date(2026, month + 1, 1) if month < 12 else dt.date(2027, 1, 1)) - dt.timedelta(days=1)
        span = (last - first).days + 1
        for _ in range(n):
            gid += 1
            reg = first + dt.timedelta(days=int(rng.integers(0, span)))
            src = 'приложение' if rng.random() < 0.42 else 'касса'
            home = shop_ids[rng.choice(6, p=[0.24, 0.12, 0.26, 0.14, 0.14, 0.10])]
            birth = int(np.clip(rng.normal(1994, 9), 1950, 2008))
            guests.append({'guest_id': f'G{gid:04d}', 'reg_date': reg, 'source': src,
                           'home_shop_id': home, 'birth_year': birth})

    # ---------- заказы гостей ----------
    orders = []  # dict: date, shop, guest, src
    for g in guests:
        reg, src = g['reg_date'], g['source']
        if src == 'касса':
            first = reg                                   # регистрация на кассе = покупка
        else:
            if rng.random() < 0.16:
                continue                                  # скачал приложение и не пришёл
            first = reg + dt.timedelta(days=int(rng.choice([0, 0, 0, 1, 2, 3, 5, 8, 12])))
        life = rng.exponential(95 if src == 'приложение' else 50)
        gap_mean = rng.gamma(4, 11 / 4)
        d = first
        while d <= END and (d - first).days <= life:
            home = g['home_shop_id']
            r = rng.random()
            if r < 0.86:
                shop = home
            elif r < 0.95:
                same = [s for s in shop_ids if city_of[s] == city_of[home] and s != home]
                shop = same[0] if same else home
            else:
                shop = shop_ids[rng.integers(0, 6)]
            orders.append({'date': d, 'shop': shop, 'guest': g['guest_id'], 'src': src})
            d = d + dt.timedelta(days=max(1, int(round(rng.exponential(gap_mean)))))

    # ---------- анонимные заказы ----------
    for d in days:
        wk = 1.12 if d.weekday() >= 5 else 1.0
        for sid, *_rest, base in SHOPS:
            lam = base * season(d) * wk
            if sid == 'UFA-1':
                lam *= 1 + 0.09 * (d.month - 3)          # молодая кофейня растёт
            for _ in range(rng.poisson(lam)):
                orders.append({'date': d, 'shop': sid, 'guest': None, 'src': None})

    # ---------- время, канал, позиции, акции ----------
    hw = HOUR_W / HOUR_W.sum()
    rows_o, rows_i = [], []
    orders.sort(key=lambda o: (o['date'], o['shop']))
    stamps = []
    for o in orders:
        h = int(rng.choice(HOURS, p=hw))
        m = int(rng.integers(0, 60))
        s = int(rng.integers(0, 60))
        stamps.append(dt.datetime(o['date'].year, o['date'].month, o['date'].day, h, m, s))
    order_idx = np.argsort(np.array(stamps, dtype='datetime64[s]'), kind='stable')
    n = 0
    for k in order_idx:
        o, ts = orders[k], stamps[k]
        n += 1
        oid = f'Z{n:06d}'
        ch = CHANNELS[rng.choice(3, p=[0.46, 0.35, 0.19])]
        d = o['date']
        # первая позиция — напиток
        w = np.array([m[5] for m in MENU if m[0] in drinks], float)
        ids = [m[0] for m in MENU if m[0] in drinks]
        w_map = dict(zip(ids, w))
        if d.month >= 5:
            w_map['M10'] = 6 * (1.3 if d.month in (7, 8) else 1.0)
        else:
            w_map['M10'] = 0
        if d.month == 4:
            w_map['M06'] *= 2.4                             # весенний раф
        if d.month in (7, 8):
            w_map['M10'] *= 1.8                             # лимонадное лето
        ww = np.array([w_map[i] for i in ids])
        lines = {}
        first_item = ids[rng.choice(len(ids), p=ww / ww.sum())]
        lines[first_item] = 1 + int(rng.random() < (0.12 if ch != 'доставка' else 0.3))
        extra = rng.choice([0, 1, 2], p=[0.58, 0.32, 0.10] if ch != 'доставка' else [0.25, 0.45, 0.30])
        for _ in range(extra):
            if rng.random() < 0.7:
                fid = list(FOOD_W)
                fw = np.array(list(FOOD_W.values()), float)
                if ts.hour < 11:
                    fw = fw * np.array([1.4, 0.8, 0.6, 2.0])  # утром — круассаны и сырники
                it = fid[rng.choice(len(fid), p=fw / fw.sum())]
            else:
                it = ids[rng.choice(len(ids), p=ww / ww.sum())]
            lines[it] = lines.get(it, 0) + 1
        # акция
        promo = None
        if o['src'] == 'приложение' and d.month == 6:
            promo = 'P2'
        elif d.month == 4 and 'M06' in lines:
            promo = 'P1'
        elif d.month in (7, 8) and 'M10' in lines:
            promo = 'P3'
        for it, q in lines.items():
            p = price[it]
            if promo == 'P2':
                p = round(p * 0.9)
            elif promo == 'P1' and it == 'M06':
                p = round(p * 0.8)
            elif promo == 'P3' and it == 'M10':
                p = round(p * 0.75)
            rows_i.append({'order_id': oid, 'item_id': it, 'qty': int(q), 'price': int(p)})
        rows_o.append({'order_id': oid, 'guest_id': o['guest'], 'shop_id': o['shop'],
                       'ordered_at': ts.strftime('%Y-%m-%d %H:%M:%S'), 'channel': ch, 'promo_id': promo})

    shops = pd.DataFrame([s[:5] for s in SHOPS], columns=['shop_id', 'city', 'name', 'opened', 'seats'])
    menu = pd.DataFrame([m[:5] for m in MENU], columns=['item_id', 'name', 'category', 'price', 'cost'])
    gdf = pd.DataFrame(guests)
    gdf['reg_date'] = gdf['reg_date'].astype(str)
    promos = pd.DataFrame(PROMOS, columns=['promo_id', 'title', 'start_date', 'end_date', 'discount_pct', 'item_id'])
    odf = pd.DataFrame(rows_o)
    idf = pd.DataFrame(rows_i)

    tables = {'shops': shops, 'menu': menu, 'guests': gdf, 'promos': promos, 'orders': odf, 'items': idf}
    for name, t in tables.items():
        t.to_csv(OUT / f'zdb_{name}.csv', index=False)

    db = OUT / 'zerno.db'
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    ddl = {
        'shops': 'shop_id TEXT PRIMARY KEY, city TEXT, name TEXT, opened TEXT, seats INTEGER',
        'menu': 'item_id TEXT PRIMARY KEY, name TEXT, category TEXT, price INTEGER, cost INTEGER',
        'guests': 'guest_id TEXT PRIMARY KEY, reg_date TEXT, source TEXT, home_shop_id TEXT REFERENCES shops, birth_year INTEGER',
        'promos': 'promo_id TEXT PRIMARY KEY, title TEXT, start_date TEXT, end_date TEXT, discount_pct INTEGER, item_id TEXT',
        'orders': 'order_id TEXT PRIMARY KEY, guest_id TEXT REFERENCES guests, shop_id TEXT REFERENCES shops, '
                  'ordered_at TEXT, channel TEXT, promo_id TEXT REFERENCES promos',
        'order_items': 'order_id TEXT REFERENCES orders, item_id TEXT REFERENCES menu, qty INTEGER, price INTEGER',
    }
    for name, cols in ddl.items():
        con.execute(f'CREATE TABLE {name} ({cols})')
        t = tables['items' if name == 'order_items' else name]
        t = t.astype(object).where(t.notna(), None)
        con.executemany(f'INSERT INTO {name} VALUES ({",".join("?" * t.shape[1])})', t.itertuples(index=False, name=None))
    con.commit()
    con.execute('VACUUM')
    con.close()
    print({k: len(v) for k, v in tables.items()}, f'zerno.db: {db.stat().st_size // 1024} КБ')


if __name__ == '__main__':
    main()
