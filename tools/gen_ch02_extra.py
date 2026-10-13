#!/usr/bin/env python3
"""Дополнительные файлы для уроков главы 2 (синтетика, детерминированная).

    python3 tools/gen_ch02_extra.py

Пишет в site/data/:
  supplier_prices.csv — прайс поставщика «как из 1С»: кодировка cp1251,
                        разделитель «;», дробная часть через запятую,
                        тысячи через пробел (урок ch02/01, параметры read_csv);
  app_events.csv      — события мобильного приложения за неделю 5–11 октября
                        2026: время — unix-время в миллисекундах по UTC,
                        как его пишет сервер (урок ch02/06, unix time
                        и часовые пояса).

История для app_events: гости открывают приложение, кладут напиток
в корзину и оформляют заказ «к определённому времени» в своей кофейне.
Пики — утро (8–9), обед (13) и вечер (18) по МЕСТНОМУ времени города.
Пермь, Тюмень, Уфа — UTC+5, Казань — UTC+3. Если не перевести время
из UTC в местное, утренний пик «уезжает» на ночь (3–4 часа UTC).
Файлы других уроков этот скрипт не трогает.
"""
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'
SEED = 2026_10_09

# ---------------------------------------------------------------- прайс поставщика
PRICES = [  # артикул, наименование, единица, цена за единицу, количество в заказе
    ('ЗК-0101', 'Зерно арабика Бразилия, 1 кг', 'кг', 1890.00, 24),
    ('ЗК-0102', 'Зерно арабика Эфиопия, 1 кг', 'кг', 2450.50, 12),
    ('ЗК-0110', 'Зерно для эспрессо-смеси, 1 кг', 'кг', 1640.00, 30),
    ('МЛ-0201', 'Молоко 3,2 %, 1 л', 'л', 92.40, 180),
    ('МЛ-0202', 'Молоко овсяное, 1 л', 'л', 214.90, 36),
    ('МЛ-0203', 'Сливки 10 %, 0,5 л', 'шт', 118.75, 40),
    ('СР-0301', 'Сироп ванильный, 1 л', 'шт', 465.00, 8),
    ('СР-0302', 'Сироп карамельный, 1 л', 'шт', 465.00, 6),
    ('СТ-0401', 'Стакан бумажный 250 мл, упаковка 1000 шт', 'уп', 3120.00, 3),
    ('СТ-0402', 'Стакан бумажный 400 мл, упаковка 1000 шт', 'уп', 3980.00, 2),
    ('КР-0501', 'Крышка для стакана, упаковка 1000 шт', 'уп', 1275.60, 4),
    ('ЧА-0601', 'Чай зелёный листовой, 0,5 кг', 'шт', 1160.00, 5),
]


def ru_money(x: float) -> str:
    """1890.0 → '1 890,00' — так число выглядит в выгрузке из 1С."""
    return f'{x:,.2f}'.replace(',', ' ').replace('.', ',')


def write_prices() -> None:
    lines = ['Артикул;Наименование;Ед.;Цена, руб.;Количество']
    for sku, name, unit, price, qty in PRICES:
        lines.append(f'{sku};{name};{unit};{ru_money(price)};{qty}')
    # cp1251 — кодировка «Windows-кириллица»: так сохраняют CSV старые
    # версии Excel и 1С. Перевод строки — как в Windows.
    (OUT / 'supplier_prices.csv').write_bytes(('\r\n'.join(lines) + '\r\n').encode('cp1251'))


# ---------------------------------------------------------------- события приложения
SHOPS = [  # shop_id, смещение от UTC в часах, относительный поток
    ('PRM-1', 5, 1.0),
    ('PRM-2', 5, 0.5),
    ('KZN-1', 3, 1.1),
    ('KZN-2', 3, 0.6),
    ('TMN-1', 5, 0.6),
    ('UFA-1', 5, 0.5),
]
# вес каждого часа МЕСТНОГО времени (0–23): кофейни работают с 8 до 22
HOUR_W = np.array([0, 0, 0, 0, 0, 0, 0, 1, 9, 8, 4, 3, 5, 7, 4, 3, 3, 4, 6, 4, 3, 2, 1, 0], float)
HOUR_W /= HOUR_W.sum()


def write_events() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    start = dt.date(2026, 10, 5)  # понедельник
    guest_pool = [f'G{n:04d}' for n in range(1, 401)]
    for day in range(7):
        date = start + dt.timedelta(days=day)
        weekend = date.weekday() >= 5
        for shop, offset, flow in SHOPS:
            n_sessions = rng.poisson(26 * flow * (0.8 if weekend else 1.0))
            for _ in range(n_sessions):
                hour = int(rng.choice(24, p=HOUR_W))
                minute = int(rng.integers(0, 60))
                second = int(rng.integers(0, 60))
                ms = int(rng.integers(0, 1000))
                local = dt.datetime(date.year, date.month, date.day, hour, minute, second, ms * 1000)
                utc = local - dt.timedelta(hours=offset)
                guest = str(rng.choice(guest_pool))
                # сессия: вход → (корзина) → (заказ), с небольшими паузами
                t = utc
                rows.append((t, shop, guest, 'вход'))
                if rng.random() < 0.62:
                    t = t + dt.timedelta(seconds=int(rng.integers(20, 240)))
                    rows.append((t, shop, guest, 'корзина'))
                    if rng.random() < 0.7:
                        t = t + dt.timedelta(seconds=int(rng.integers(30, 300)))
                        rows.append((t, shop, guest, 'заказ'))
    df = pd.DataFrame(rows, columns=['utc', 'shop_id', 'guest_id', 'event'])
    df = df.sort_values('utc', kind='stable').reset_index(drop=True)
    epoch = dt.datetime(1970, 1, 1)
    df['ts'] = [int((u - epoch) / dt.timedelta(milliseconds=1)) for u in df['utc']]
    df.insert(0, 'event_id', [f'E{n:05d}' for n in range(1, len(df) + 1)])
    df[['event_id', 'ts', 'shop_id', 'guest_id', 'event']].to_csv(OUT / 'app_events.csv', index=False)


if __name__ == '__main__':
    write_prices()
    write_events()
    print('ok: supplier_prices.csv, app_events.csv')
