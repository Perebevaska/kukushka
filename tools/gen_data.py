#!/usr/bin/env python3
"""Учебные данные сети кофеен «Зерно» (синтетика, детерминированная).

    uv run tools/gen_data.py      # → site/data/orders.csv, site/data/menu.txt

В orders.csv специально есть «грязь» для уроков: пустая сумма, прочерк, сумма с пробелом
и один повторённый заказ.
"""
import csv
import datetime as dt
import math
import random

import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data'

MENU = {'Латте': 210, 'Капучино': 190, 'Раф': 260, 'Американо': 150, 'Флэт уайт': 230, 'Мокко': 240}
CITIES = ['Пермь', 'Пермь', 'Казань', 'Казань', 'Тюмень', 'Уфа']


def main() -> None:
    rnd = random.Random(2026)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    day0 = dt.date(2026, 9, 1)
    for i in range(1, 41):
        date = day0 + dt.timedelta(days=rnd.randrange(0, 30))
        city = rnd.choice(CITIES)
        drink = rnd.choice(list(MENU))
        qty = rnd.choice([1, 1, 1, 2, 2, 3])
        rows.append([f'Z-{1000 + i}', date.isoformat(), city, drink, str(MENU[drink] * qty)])
    rows.sort(key=lambda r: (r[1], r[0]))
    # грязь
    rows[5][4] = ''
    rows[17][4] = '—'
    rows[28][4] = '1 250'
    rows.insert(12, list(rows[11]))          # повторённый заказ
    with open(OUT / 'orders.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['order_id', 'date', 'city', 'drink', 'amount'])
        w.writerows(rows)
    (OUT / 'menu.txt').write_text(''.join(f'{k}\n' for k in MENU) + '\n', encoding='utf-8')
    print(f'orders.csv: {len(rows)} строк, menu.txt: {len(MENU)} позиций')
    gen_chapter2(rnd)
    gen_chapter3(random.Random(3003))   # свой генератор — данные глав 1–2 не меняются
    home_orders(7)                      # гости из clients_raw.csv заказывают в основном в своём городе
    gen_chapter4(random.Random(4004))
    gen_chapter5(random.Random(5010))
    gen_chapter6(random.Random(6006))
    gen_chapter7(random.Random(7007))
    gen_chapter8(random.Random(8033))
    gen_chapter9(random.Random(9009))
    gen_chapter10(random.Random(10010))
    gen_chapter12(random.Random(12012))
    gen_chapter13(random.Random(13013))
    gen_chapter14(14014)
    gen_chapter15(random.Random(15015))


# ---------- глава 2: три месяца продаж ----------

SHOPS = [  # shop_id, город, название, открыта, мест
    ('PRM-1', 'Пермь', 'Ленина', '2021-03-01', 24),
    ('PRM-2', 'Пермь', 'Компрос', '2023-06-15', 16),
    ('KZN-1', 'Казань', 'Баумана', '2022-04-01', 30),
    ('KZN-2', 'Казань', 'Кремлёвская', '2024-09-01', 18),
    ('TMN-1', 'Тюмень', 'Республики', '2023-02-01', 20),
    ('UFA-1', 'Уфа', 'Ленина', '2025-11-01', 22),
    ('EKB-1', 'Екатеринбург', 'Вайнера', '2026-10-15', 26),   # открылась после периода — для LEFT JOIN
]
MENU2 = [  # напиток, категория, цена S, себестоимость S
    ('Эспрессо', 'кофе', 120, 28), ('Американо', 'кофе', 150, 30), ('Капучино', 'кофе', 190, 45),
    ('Латте', 'кофе', 210, 50), ('Флэт уайт', 'кофе', 230, 52), ('Раф', 'кофе', 260, 70),
    ('Мокко', 'кофе', 240, 65), ('Какао', 'не кофе', 180, 40), ('Чай', 'не кофе', 120, 15),
    ('Матча', 'не кофе', 250, 80), ('Сезонный', 'кофе', 280, 75),
]
SIZE_K = {'S': 1.0, 'M': 1.25, 'L': 1.5}


def gen_chapter2(rnd: random.Random) -> None:
    with open(OUT / 'shops.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['shop_id', 'city', 'name', 'opened', 'seats'])
        w.writerows(SHOPS)
    with open(OUT / 'menu.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['drink', 'category', 'price_s', 'cost_s'])
        w.writerows(MENU2)
    shops = [s for s in SHOPS if s[0] != 'EKB-1']
    shop_w = {'PRM-1': 5, 'PRM-2': 2, 'KZN-1': 5, 'KZN-2': 3, 'TMN-1': 3, 'UFA-1': 2}
    drink_w = {'Эспрессо': 3, 'Американо': 8, 'Капучино': 9, 'Латте': 10, 'Флэт уайт': 6, 'Раф': 5,
               'Мокко': 3, 'Какао': 3, 'Чай': 4, 'Матча': 2, 'Сезонный': 0}
    prices = {d: p for d, _c, p, _k in MENU2}
    clients = [f'C{1000 + i}' for i in range(260)]
    rows = []
    day = dt.date(2026, 9, 1)
    n = 0
    while day <= dt.date(2026, 11, 30):
        wd = day.weekday()
        for sid, *_ in shops:
            base = shop_w[sid] * (1.35 if wd >= 5 else 1.0) * (1.1 if day.month == 11 else 1.0)
            k = int(rnd.gauss(base, 1.2) + 0.5)
            for _ in range(max(0, k)):
                n += 1
                hour = rnd.choices(range(8, 22), weights=[5, 9, 7, 5, 6, 7, 5, 4, 4, 5, 6, 5, 3, 2])[0]
                ts = dt.datetime(day.year, day.month, day.day, hour, rnd.randrange(60))
                dw = dict(drink_w)
                if day >= dt.date(2026, 11, 1):
                    dw['Сезонный'] = 6        # сезонный напиток появился в ноябре
                drink = rnd.choices(list(dw), weights=list(dw.values()))[0]
                size = rnd.choices(['S', 'M', 'L'], weights=[3, 5, 2])[0]
                qty = rnd.choices([1, 2, 3], weights=[8, 3, 1])[0]
                amount = round(prices[drink] * SIZE_K[size]) * qty
                client = rnd.choice(clients) if rnd.random() < 0.6 else ''
                channel = rnd.choices(['зал', 'с собой', 'доставка'], weights=[5, 4, 2])[0]
                rows.append([f'O-{n:05d}', ts.strftime('%Y-%m-%d %H:%M'), sid, drink, size, qty, amount, client, channel])
        day += dt.timedelta(days=1)
    with open(OUT / 'orders_3m.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['order_id', 'datetime', 'shop_id', 'drink', 'size', 'qty', 'amount', 'client_id', 'channel'])
        w.writerows(rows)
    print(f'orders_3m.csv: {len(rows)} строк, shops.csv: {len(SHOPS)}, menu.csv: {len(MENU2)}')



# ---------- глава 3: грязные выгрузки для предобработки ----------

NAMES_M = ['Иван', 'Алексей', 'Дмитрий', 'Сергей', 'Артём', 'Максим', 'Павел', 'Роман', 'Тимур', 'Ильдар', 'Олег', 'Никита']
NAMES_F = ['Анна', 'Мария', 'Елена', 'Ольга', 'Дарья', 'Алина', 'Наталья', 'Ксения', 'Гульнара', 'Юлия', 'Софья', 'Ирина']
CITY_W = {'Пермь': 30, 'Казань': 30, 'Тюмень': 14, 'Уфа': 12, 'Екатеринбург': 8, 'Москва': 4}
SOURCES = {  # каноническое значение → варианты записи (вес)
    'соцсети': [('соцсети', 10), ('Соцсети', 3), ('соц. сети', 2)],
    'друзья': [('друзья', 8), ('от друзей', 3), ('Друзья ', 2)],
    'мимо': [('проходил мимо', 6), ('мимо', 3)],
    'карты': [('2ГИС', 3), ('Яндекс Карты', 3)],
    'реклама': [('реклама', 4)],
}


def _w(rnd, pairs):
    return rnd.choices([p for p, _ in pairs], weights=[w for _, w in pairs])[0]


def _city_text(rnd, city):
    if city == 'Екатеринбург' and rnd.random() < 0.35:
        return rnd.choice(['Екб', 'ЕКБ'])
    return _w(rnd, [(city, 70), (city.lower(), 8), (f' {city} ', 4), (f'{city} ', 4),
                    (f'г. {city}', 6), (f'г.{city}', 2)])


def _phone_text(rnd, d):
    a, b, c, e = d[:3], d[3:6], d[6:8], d[8:]
    return _w(rnd, [(f'+7 {a} {b}-{c}-{e}', 35), (f'8 ({a}) {b}-{c}-{e}', 20), (f'8{d}', 20),
                    (f'+7{d}', 15), (f'{a} {b} {c} {e}', 6), (f'+7 ({a}) {b}{c}{e}', 4)])


def _bonus_text(rnd, v):
    if v >= 1000 and rnd.random() < 0.6:
        return f'{v // 1000} {v % 1000:03d}'
    return str(v)


def gen_chapter3(rnd: random.Random) -> None:
    rows = []
    phones = set()
    for i in range(290):            # C1000–C1259 есть в orders_3m.csv, C1260–C1289 — без заказов
        cid = f'C{1000 + i}'
        male = rnd.random() < 0.45
        name = rnd.choice(NAMES_M if male else NAMES_F)
        if rnd.random() < 0.05:
            name = name.upper()
        g = _w(rnd, [('М', 70), ('м', 10), ('муж', 8), ('', 7)]) if male else \
            _w(rnd, [('Ж', 70), ('ж', 10), ('жен', 8), ('', 7)])
        born = dt.date(1966, 1, 1) + dt.timedelta(days=rnd.randrange(0, 42 * 365))
        r = rnd.random()
        if r < 0.70:
            bd = born.isoformat()
        elif r < 0.88:
            bd = born.strftime('%d.%m.%Y')
        elif r < 0.95:
            bd = ''
        else:
            bd = 'не указано'
        city = rnd.choices(list(CITY_W), weights=list(CITY_W.values()))[0]
        ct = '' if rnd.random() < 0.06 else _city_text(rnd, city)
        while True:
            d = '9' + ''.join(str(rnd.randrange(10)) for _ in range(9))
            if d not in phones:
                phones.add(d)
                break
        ph = '' if rnd.random() < 0.04 else _phone_text(rnd, d)
        signup = dt.date(2024, 1, 10) + dt.timedelta(days=rnd.randrange(0, 1040))
        bonus = int(rnd.expovariate(1 / 600)) // 10 * 10
        r = rnd.random()
        bt = '' if r < 0.05 else ('—' if r < 0.08 else _bonus_text(rnd, bonus))
        canon = rnd.choices(list(SOURCES) + [''], weights=[15, 13, 9, 6, 4, 6])[0]
        src = _w(rnd, SOURCES[canon]) if canon else ''
        if rnd.random() < 0.03:
            src = rnd.choice(['коллега', 'бариста посоветовал', 'работаю рядом'])
        rows.append([cid, name, g, bd, ct, ph, signup.isoformat(), bt, src])
    # аномалии
    for k, v in [(7, '1900-01-01'), (61, '1900-01-01'), (140, '1900-01-01'), (203, '2031-04-05')]:
        rows[k][3] = v
    rows[33][7] = '-50'
    rows[188][7] = '-120'
    rows[95][7] = '99999'
    # тот же гость зарегистрировался повторно: id записан иначе, анкета новее
    for k in [12, 48, 77, 131, 166, 222]:
        r = list(rows[k])
        r[0] = rnd.choice([r[0].lower(), f' {r[0]}', f'{r[0]} '])
        r[6] = (dt.date.fromisoformat(r[6]) + dt.timedelta(days=rnd.randrange(30, 200))).isoformat()
        r[7] = str(int(rnd.expovariate(1 / 600)) // 10 * 10)
        rows.append(r)
    # тот же телефон под новой картой (новые id, заказов нет)
    for j, k in enumerate([20, 115, 250]):
        r = list(rows[k])
        r[0] = f'C{1290 + j}'
        r[6] = (dt.date.fromisoformat(r[6]) + dt.timedelta(days=rnd.randrange(10, 90))).isoformat()
        r[7] = '0'
        if r[5]:
            r[5] = _phone_text(rnd, ''.join(ch for ch in r[5] if ch.isdigit())[-10:])
        rows.append(r)
    # двойная выгрузка — полные копии строк
    for k in [3, 40, 90, 150, 199, 240, 270, 281]:
        rows.append(list(rows[k]))
    rnd.shuffle(rows)
    with open(OUT / 'clients_raw.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['client_id', 'name', 'gender', 'birth_date', 'city', 'phone', 'signup_date', 'bonus', 'source'])
        w.writerows(rows)

    # выгрузка новой кассы за первую неделю декабря: «;» и десятичная запятая
    prices = {d: p for d, _c, p, _k in MENU2}
    drink_w = {'Эспрессо': 3, 'Американо': 8, 'Капучино': 9, 'Латте': 10, 'Флэт уайт': 6, 'Раф': 5,
               'Мокко': 3, 'Какао': 4, 'Чай': 5, 'Матча': 2, 'Сезонный': 6}
    typo = {'Капучино': 'Каппучино', 'Флэт уайт': 'Флет уайт', 'Американо': 'Амерекано'}
    pos = []
    n = 0
    day = dt.date(2026, 12, 1)
    while day <= dt.date(2026, 12, 7):
        for sid in ['PRM-1', 'PRM-2', 'KZN-1', 'KZN-2', 'TMN-1', 'UFA-1', 'EKB-1']:
            for _ in range(max(0, int(rnd.gauss(7, 2)))):
                n += 1
                ts = dt.datetime(day.year, day.month, day.day, rnd.randrange(8, 22), rnd.randrange(60))
                drink = rnd.choices(list(drink_w), weights=list(drink_w.values()))[0]
                size = rnd.choices(['S', 'M', 'L'], weights=[3, 5, 2])[0]
                price = prices[drink] * SIZE_K[size]
                qty = rnd.choices([1, 2, 3], weights=[8, 3, 1])[0]
                disc = rnd.choices(['0%', '10%', '15%', ''], weights=[12, 3, 1, 2])[0]
                dt_txt = _w(rnd, [(drink, 80), (drink.lower(), 8), (drink + ' ', 6)])
                if drink in typo and rnd.random() < 0.12:
                    dt_txt = typo[drink]
                s_txt = _w(rnd, [(sid, 90), (sid.lower(), 6), (sid.replace('-', ' '), 4)])
                pos.append([ts, ts.strftime('%d.%m.%Y %H:%M'), s_txt, dt_txt, size, qty,
                            f'{price:.2f}'.replace('.', ','), disc])
        day += dt.timedelta(days=1)
    pos.sort(key=lambda r: r[0])
    for i, r in enumerate(pos):
        r[0] = f'D-{i + 1:04d}'
    pos[17][5] = 0
    pos[123][5] = 0
    pos[201][5] = 40          # заказ в офис — правда или ошибка?
    for k in [10, 55, 170, 260]:
        pos.insert(k + 1, list(pos[k]))
    with open(OUT / 'pos_december.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['id', 'time', 'shop', 'drink', 'size', 'qty', 'price', 'discount'])
        w.writerows(pos)

    # отзывы гостей
    good = ['Очень вкусный {d}, спасибо!', 'Лучший {d} в городе', '{d} отличный, бариста приветливые',
            'Уютно, вкусно, вернусь', 'Быстро и вкусно', 'Взяла {d} с собой — понравилось']
    bad = ['{d} был холодный', 'Долго ждали заказ, минут 15', 'Очередь на кассе, {d} остыл',
           'Дорого для такого размера', 'Перепутали заказ: просил {d}', 'Холодный {d} и долгое ожидание',
           'ДОЛГО! Опаздывал на работу']
    mid = ['Нормально, но {d} мог быть горячее', 'Ничего особенного', 'Неплохо, но дорого']
    reviews = []
    for i in range(150):
        day = dt.date(2026, 9, 1) + dt.timedelta(days=rnd.randrange(0, 91))
        sid = rnd.choice(['PRM-1', 'PRM-2', 'KZN-1', 'KZN-2', 'TMN-1', 'UFA-1'])
        d = rnd.choice(['латте', 'капучино', 'раф', 'американо', 'флэт уайт', 'какао', 'чай'])
        mood = rnd.choices(['g', 'b', 'm'], weights=[6, 3, 2])[0]
        stars = {'g': rnd.choice([5, 5, 4]), 'b': rnd.choice([1, 2, 2, 3]), 'm': rnd.choice([3, 3, 4])}[mood]
        text = rnd.choice({'g': good, 'b': bad, 'm': mid}[mood]).format(d=d)
        if rnd.random() < 0.2:
            text = text[0].lower() + text[1:]
        rating = _w(rnd, [(str(stars), 75), (f'{stars}/5', 12), (f'{stars} из 5', 5), ('', 8)])
        reviews.append([i, day.isoformat(), sid, rating, text])
    reviews.sort(key=lambda r: (r[1], r[0]))
    for i, r in enumerate(reviews):
        r[0] = f'R-{i + 1:03d}'
    with open(OUT / 'reviews.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['review_id', 'date', 'shop_id', 'rating', 'text'])
        w.writerows(reviews)
    print(f'clients_raw.csv: {len(rows)}, pos_december.csv: {len(pos)}, reviews.csv: {len(reviews)}')



# ---------- глава 2 + 3: гости заказывают в основном в своём городе ----------

def home_orders(seed: int, p_home: float = 0.97) -> None:
    """Переставляет метки client_id между заказами orders_3m.csv.

    gen_chapter2 выбирает гостя заказа случайно, без оглядки на его город из clients_raw.csv.
    Здесь метки гостей перекладываются так, чтобы заказ с вероятностью p_home достался гостю
    из города кофейни. Число заказов у каждого гостя и всё остальное в заказе (время, кофейня,
    напиток, сумма, канал) не меняются — агрегаты по кофейням, городам, дням, напиткам прежние.
    Город гостя — после той же чистки, что в уроках главы 3 (последняя анкета по signup_date).
    """
    import pandas as pd
    raw = pd.read_csv(OUT / 'clients_raw.csv').drop_duplicates().copy()
    raw['client_id'] = raw['client_id'].str.strip().str.upper()
    raw['city'] = (raw['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                   .replace({'екб': 'екатеринбург'}).str.capitalize())
    raw['signup_date'] = pd.to_datetime(raw['signup_date'])
    c = raw.sort_values('signup_date').drop_duplicates('client_id', keep='last')
    home = {k: v for k, v in zip(c['client_id'], c['city']) if isinstance(v, str)}

    with open(OUT / 'orders_3m.csv', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    hdr, rows = rows[0], rows[1:]
    ci = hdr.index('client_id')
    shop_city = {sid: city for sid, city, *_ in SHOPS}
    rng = np.random.default_rng(seed)
    idx = [i for i, r in enumerate(rows) if r[ci] in home]
    pool = [rows[i][ci] for i in idx]
    rng.shuffle(pool)
    for i in rng.permutation(idx):
        city = shop_city[rows[i][2]]
        cand = [j for j, cl in enumerate(pool) if home[cl] == city]
        if cand and rng.random() < p_home:
            j = cand[0]
        else:
            oth = [j for j, cl in enumerate(pool) if home[cl] != city]
            j = (oth or cand)[0]
        rows[i][ci] = pool.pop(j)
    with open(OUT / 'orders_3m.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(rows)
    n_home = sum(home[rows[i][ci]] == shop_city[rows[i][2]] for i in idx)
    print(f'orders_3m.csv: гостям переставлены заказы, в своём городе {n_home} из {len(idx)}')



# ---------- глава 4: доставка для исследовательского анализа ----------

WEATHER = {9: {'ясно': 55, 'облачно': 30, 'дождь': 15},
           10: {'ясно': 30, 'облачно': 35, 'дождь': 35},
           11: {'ясно': 20, 'облачно': 30, 'дождь': 10, 'снег': 40}}


def gen_chapter4(rnd: random.Random) -> None:
    import math
    rows = []
    day = dt.date(2026, 9, 1)
    hours = list(range(9, 22))
    hour_w = [3, 4, 6, 9, 9, 7, 5, 5, 6, 9, 9, 6, 3]
    shops = ['PRM-1', 'PRM-2', 'KZN-1', 'KZN-2', 'TMN-1', 'UFA-1']
    shop_w = [5, 3, 5, 3, 3, 2]
    while day <= dt.date(2026, 11, 30):
        weather_day = rnd.choices(list(WEATHER[day.month]), weights=list(WEATHER[day.month].values()))[0]
        n = int(rnd.gauss(20 if day.weekday() < 5 else 25, 3))
        for _ in range(max(0, n)):
            hour = rnd.choices(hours, weights=hour_w)[0]
            ts = dt.datetime(day.year, day.month, day.day, hour, rnd.randrange(60))
            shop = rnd.choices(shops, weights=shop_w)[0]
            weather = weather_day if rnd.random() < 0.85 else rnd.choice(list(WEATHER[day.month]))
            dist = min(15.0, max(0.3, math.exp(rnd.gauss(math.log(2.5), 0.6))))
            if dist < 1.5:
                courier = rnd.choices(['пеший', 'вело', 'авто'], weights=[8, 2, 1])[0]
            elif dist < 5:
                courier = rnd.choices(['пеший', 'вело', 'авто'], weights=[1, 7 if weather != 'снег' else 3, 3])[0]
            else:
                courier = rnd.choices(['вело', 'авто'], weights=[2 if weather != 'снег' else 0.5, 8])[0]
            peak = hour in (12, 13, 18, 19)
            speed = {'пеший': 5.0, 'вело': 14.0, 'авто': 24.0}[courier]
            if weather == 'дождь':
                speed *= 0.85
            if weather == 'снег':
                speed *= 0.6 if courier == 'вело' else 0.75
            if courier == 'авто' and peak:
                speed *= 0.7
            items = rnd.choices([1, 2, 3, 4, 5, 6], weights=[30, 30, 18, 10, 7, 5])[0]
            prep = 6 + 1.5 * items + rnd.gauss(0, 2) + (5 if peak else 0) + (4 if shop == 'KZN-2' else 0)
            actual = prep + dist / speed * 60 + 3 + rnd.expovariate(1 / 4)
            promised = 30 if dist < 2 else (45 if dist < 5 else 60)
            amount = int(sum(rnd.choice([150, 190, 210, 230, 260, 180, 120]) * rnd.choice([1, 1.25, 1.5]) for _ in range(items)))
            late = actual - promised
            rating = ''
            if rnd.random() < 0.55:
                r = 5 - max(0, late) / 8 + rnd.gauss(0, 0.7)
                rating = str(int(min(5, max(1, round(r)))))
            rows.append([ts, shop, courier, round(dist, 1), weather, items, amount, promised, round(actual), rating])
        day += dt.timedelta(days=1)
    rows.sort(key=lambda r: r[0])
    # аномалии: не закрытые заказы, сбой часов, забытые закрыть
    idx = rnd.sample(range(len(rows)), 45)
    for k in idx[:25]:
        rows[k][8] = ''
    for k in idx[25:31]:
        rows[k][8] = rnd.choice([0, -3, -12, 0, 1, -5])
    for k in idx[31:36]:
        rows[k][8] = rnd.randrange(300, 1500)
    with open(OUT / 'deliveries.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['delivery_id', 'created', 'shop_id', 'courier', 'distance_km', 'weather', 'items',
                    'amount', 'promised_min', 'actual_min', 'rating'])
        for i, r in enumerate(rows):
            w.writerow([f'DL-{i + 1:05d}', r[0].strftime('%Y-%m-%d %H:%M')] + r[1:])
    print(f'deliveries.csv: {len(rows)}')



# ---------- глава 5: A/B-тесты ----------

def _delivery_time(rnd, dist, courier, weather, hour, items):
    """Та же модель времени, что в главе 4 (без кофейни)."""
    import math
    peak = hour in (12, 13, 18, 19)
    speed = {'пеший': 5.0, 'вело': 14.0, 'авто': 24.0}[courier]
    if weather == 'дождь':
        speed *= 0.85
    if weather == 'снег':
        speed *= 0.6 if courier == 'вело' else 0.75
    if courier == 'авто' and peak:
        speed *= 0.7
    prep = 6 + 1.5 * items + rnd.gauss(0, 2) + (5 if peak else 0)
    return prep + dist / speed * 60 + 3 + rnd.expovariate(1 / 4)


def gen_chapter5(rnd: random.Random) -> None:
    import math
    cities = ['Пермь', 'Казань', 'Тюмень', 'Уфа']
    city_w = [35, 35, 15, 15]
    # 1) пуш-напоминание: контроль A без пуша, B — с пушем
    rows = []
    for i in range(6000):
        g = 'A' if rnd.random() < 0.5 else 'B'
        city = rnd.choices(cities, weights=city_w)[0]
        p = 0.09 if g == 'A' else 0.11
        ordered = int(rnd.random() < p)
        n = 1 + (int(rnd.expovariate(1 / 0.5)) if ordered else 0) if ordered else 0
        rev = sum(int(math.exp(rnd.gauss(math.log(330), 0.45))) for _ in range(n))
        rows.append([f'U{i + 1:05d}', g, city, ordered, n, rev])
    with open(OUT / 'ab_push.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['user_id', 'group', 'city', 'ordered', 'orders', 'revenue'])
        w.writerows(rows)

    # 2) новое обещание доставки: в B пешим зонам (до 2 км) обещаем 40 минут вместо 30
    rows = []
    day0 = dt.date(2026, 12, 1)
    hours = list(range(9, 22))
    hour_w = [3, 4, 6, 9, 9, 7, 5, 5, 6, 9, 9, 6, 3]
    k = 0
    for d in range(21):
        day = day0 + dt.timedelta(days=d)
        weather_day = rnd.choices(['ясно', 'облачно', 'снег'], weights=[25, 35, 40])[0]
        for _ in range(int(rnd.gauss(380, 30))):
            k += 1
            g = 'A' if rnd.random() < 0.5 else 'B'
            hour = rnd.choices(hours, weights=hour_w)[0]
            ts = dt.datetime(day.year, day.month, day.day, hour, rnd.randrange(60))
            city = rnd.choices(cities, weights=city_w)[0]
            dist = round(min(15.0, max(0.3, math.exp(rnd.gauss(math.log(2.5), 0.6)))), 1)
            promise = 30 if dist < 2 else (45 if dist < 5 else 60)
            if g == 'B' and dist < 2:
                promise = 40
            conv = 0.36 - (promise - 30) * 0.0035 if dist < 2 else 0.34 - (promise - 45) * 0.002
            ordered = int(rnd.random() < conv)
            courier = actual = rating = late = ''
            amount = 0
            if ordered:
                weather = weather_day if rnd.random() < 0.85 else rnd.choice(['ясно', 'облачно', 'снег'])
                if dist < 1.5:
                    courier = rnd.choices(['пеший', 'вело', 'авто'], weights=[8, 2, 1])[0]
                elif dist < 5:
                    courier = rnd.choices(['пеший', 'вело', 'авто'], weights=[1, 7 if weather != 'снег' else 3, 3])[0]
                else:
                    courier = rnd.choices(['вело', 'авто'], weights=[2 if weather != 'снег' else 0.5, 8])[0]
                items = rnd.choices([1, 2, 3, 4, 5, 6], weights=[30, 30, 18, 10, 7, 5])[0]
                a = _delivery_time(rnd, dist, courier, weather, hour, items)
                actual = round(a)
                late = int(actual > promise)
                amount = int(sum(rnd.choice([150, 190, 210, 230, 260, 180, 120]) * rnd.choice([1, 1.25, 1.5]) for _ in range(items)))
                if rnd.random() < 0.55:
                    r = 5 - max(0, actual - promise) / 8 + rnd.gauss(0, 0.7)
                    rating = str(int(min(5, max(1, round(r)))))
            rows.append([f'S{k:06d}', ts.strftime('%Y-%m-%d %H:%M'), g, city, dist, promise, ordered,
                         courier, amount, actual, late, rating])
    with open(OUT / 'ab_promise.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['session_id', 'ts', 'group', 'city', 'distance_km', 'promise_min', 'ordered',
                    'courier', 'amount', 'actual_min', 'late', 'rating'])
        w.writerows(rows)
    print(f'ab_push.csv: 6000, ab_promise.csv: {len(rows)}')


# ---------- глава 6: кто из гостей уйдёт ----------

def gen_chapter6(rnd: random.Random) -> None:
    """guests_churn.csv: гости программы лояльности на 1 декабря 2026.
    churned — не пришёл ни разу за следующие 60 дней. card_blocked — утечка:
    карту блокируют после 60 дней без визитов, то есть уже по итогам периода."""
    import math
    cities = {'Пермь': 32, 'Казань': 34, 'Тюмень': 18, 'Уфа': 16}
    rows = []
    for i in range(2400):
        city = rnd.choices(list(cities), weights=list(cities.values()))[0]
        tenure = max(1, int(math.exp(rnd.gauss(math.log(14), 0.8))))      # месяцев в программе
        tenure = min(tenure, 60)
        app = 1 if rnd.random() < 0.45 else 0
        habit = rnd.gauss(0, 1)                                            # скрытая «привычка»
        rate = math.exp(1.6 + 0.6 * habit + 0.25 * app)                    # визитов за 90 дней в среднем
        visits = max(0, int(rnd.gauss(rate, math.sqrt(rate))))
        if visits == 0:
            days_since = rnd.randrange(91, 200)
            avg_check = ''
        else:
            days_since = min(90, int(rnd.expovariate(1 / max(2.0, 75 / (visits + 1)))))
            avg_check = int(max(120, rnd.gauss(330 + 40 * (city == 'Казань'), 90)))
        delivery_share = round(min(1.0, max(0.0, rnd.betavariate(1.2, 4) + (0.15 if app else 0))), 2) if visits else 0.0
        fav = rnd.choices(['кофе', 'не кофе', 'еда'], weights=[6, 2, 2])[0]
        promo = min(visits, int(rnd.expovariate(1 / (1.5 + 1.5 * app))))
        complaints = 1 if rnd.random() < 0.06 + 0.08 * delivery_share else 0
        if rnd.random() < 0.02:
            complaints += 1
        # логика ухода: нелинейно — давность, частота, жалобы×доставка, новички
        z = (-0.2
             + 2.2 * (1 - math.exp(-days_since / 35)) - 0.9
             - 0.35 * math.log1p(visits)
             + 1.6 * complaints * (0.3 + delivery_share * 3)
             + (1.2 if tenure <= 3 else 0)
             - 0.4 * app
             - 0.2 * min(promo, 4) / 4
             + (0.9 if city == "Тюмень" and visits < 4 else 0)
             + rnd.gauss(0, 0.35))
        churned = 1 if rnd.random() < 1 / (1 + math.exp(-2.2 * z)) else 0
        card_blocked = 1 if churned and rnd.random() < 0.93 else (1 if rnd.random() < 0.01 else 0)
        rows.append([f'G-{10001 + i}', city, tenure, app, visits, days_since, avg_check,
                     delivery_share, fav, promo, complaints, card_blocked, churned])
    with open(OUT / 'guests_churn.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['guest_id', 'city', 'tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check',
                    'delivery_share', 'fav_category', 'promo_used', 'complaints', 'card_blocked', 'churned'])
        w.writerows(rows)
    print(f'guests_churn.csv: {len(rows)}')


# ---------- глава 7: заявки на кейтеринг ----------

def gen_chapter7(rnd: random.Random) -> None:
    """catering_leads.csv: заявки компаний на кофе-кейтеринг (январь 2026 — сентябрь 2026).
    converted — заключили договор (≈ 12 %). contract_rub — утечка: сумма договора,
    известна только после сделки (пусто, если сделки нет)."""
    import math
    channels = {'сайт': 40, 'звонок': 20, 'рекомендация': 12, 'соцсети': 18, 'выставка': 6, 'тендер': 4}
    events = {'конференция': 25, 'тренинг': 30, 'корпоратив': 20, 'выставка': 10, 'свадьба': 8, 'другое': 7}
    cities = {'Пермь': 30, 'Казань': 34, 'Тюмень': 18, 'Уфа': 14, 'Екатеринбург': 4}
    managers = ['Анна', 'Ильдар', 'Олег', 'Софья', 'Тимур']
    rows = []
    day0 = dt.date(2026, 1, 9)
    for i in range(3000):
        created = day0 + dt.timedelta(days=rnd.randrange(0, 260))
        hour = rnd.choices(range(8, 23), weights=[3, 6, 8, 9, 8, 6, 7, 7, 6, 5, 4, 3, 2, 2, 1])[0]
        ch = rnd.choices(list(channels), weights=list(channels.values()))[0]
        ev = rnd.choices(list(events), weights=list(events.values()))[0]
        city = rnd.choices(list(cities), weights=list(cities.values()))[0]
        size = rnd.choices(['до 50', '50–250', '250–1000', '1000+', ''], weights=[30, 32, 20, 10, 8])[0]
        guests = int(min(800, max(8, math.exp(rnd.gauss(math.log(45), 0.75)))))
        budget = int(round(max(150, rnd.gauss(520, 180)), -1)) if rnd.random() > 0.27 else ''
        lead_days = max(1, int(math.exp(rnd.gauss(math.log(14), 0.8))))   # дней до события
        mgr = rnd.choice(managers)
        resp = rnd.expovariate(1 / (2.5 if mgr != 'Олег' else 7.0))       # часы до первого ответа
        if hour >= 19:
            resp += rnd.uniform(8, 14)                                     # вечерняя заявка ждёт утра
        resp = round(resp, 1)
        repeat = 1 if rnd.random() < (0.35 if ch == 'рекомендация' else 0.12) else 0
        tasting = 1 if rnd.random() < 0.18 else 0                          # просили дегустацию
        z = (-1.9
             + {'сайт': 0, 'звонок': 0.5, 'рекомендация': 1.2, 'соцсети': -0.4, 'выставка': 0.3, 'тендер': -0.8}[ch]
             + {'конференция': 0.3, 'тренинг': 0.2, 'корпоратив': 0.4, 'выставка': 0.1, 'свадьба': -0.6, 'другое': -0.3}[ev]
             + 1.4 * repeat + 0.9 * tasting
             - 0.8 * math.log1p(resp)                                    # быстрый ответ решает
             + (0.6 if 5 <= lead_days <= 30 else (-0.7 if lead_days < 3 else 0))
             + (0.0 if budget == '' else (0.5 if budget >= 450 else -0.5))
             + (-0.5 if budget == '' and ch == 'соцсети' else 0)
             + {'до 50': -0.3, '50–250': 0.2, '250–1000': 0.4, '1000+': 0.1, '': -0.4}[size]
             - 0.25 * abs(math.log(guests / 60))
             + rnd.gauss(0, 0.3))
        conv = 1 if rnd.random() < 1 / (1 + math.exp(-1.7 * z)) else 0
        contract = int(round(guests * (budget or 450) * rnd.uniform(0.85, 1.2), -2)) if conv else ''
        rows.append([f'L-{20001 + i}', f'{created.isoformat()} {hour:02d}:{rnd.randrange(60):02d}', ch, ev, city,
                     size, guests, budget, lead_days, mgr, resp, repeat, tasting, contract, conv])
    rows.sort(key=lambda r: r[1])
    for k, r in enumerate(rows):
        r[0] = f'L-{20001 + k}'
    with open(OUT / 'catering_leads.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['lead_id', 'created', 'channel', 'event_type', 'city', 'company_size', 'guests', 'budget_pp',
                    'days_to_event', 'manager', 'response_hours', 'repeat_client', 'tasting', 'contract_rub', 'converted'])
        w.writerows(rows)
    print(f'catering_leads.csv: {len(rows)}')


# ---------- глава 8: где поставить кофейные автоматы ----------

def gen_chapter8(rnd: random.Random) -> None:
    """sites.csv: обследованные места для кофейных автоматов в трёх городах.
    profit_k — фактическая годовая прибыль автомата (тыс. ₽) по данным пилота / похожих мест.
    Города устроены по-разному: в Екатеринбурге средняя прибыль выше, но она хуже предсказуема."""
    import math
    cfg = {  # город: (среднее смещение, шум, сила связи с трафиком)
        'Пермь': (0, 38, 1.0),
        'Казань': (10, 60, 0.85),
        'Екатеринбург': (30, 110, 0.6),
    }
    kinds = {'бизнес-центр': 40, 'вуз': 15, 'больница': 12, 'вокзал': 8, 'ТЦ': 15, 'завод': 10}
    kind_eff = {'бизнес-центр': 25, 'вуз': 15, 'больница': 5, 'вокзал': 30, 'ТЦ': -10, 'завод': -5}
    rows = []
    n = 0
    for city, (shift, noise, k_tr) in cfg.items():
        for _ in range(1500):
            n += 1
            kind = rnd.choices(list(kinds), weights=list(kinds.values()))[0]
            traffic = int(min(6000, max(80, math.exp(rnd.gauss(math.log(700), 0.6)))))
            offices = max(0, int(rnd.gauss(6, 4))) if kind in ('бизнес-центр', 'ТЦ') else max(0, int(rnd.gauss(2, 2)))
            competitors = min(8, int(rnd.expovariate(1 / 1.6)))
            rent_k = int(round(max(24, rnd.gauss(60 + 25 * (kind == 'ТЦ') + 20 * (kind == 'вокзал'), 18)), -1) / 1)
            hours24 = 1 if rnd.random() < (0.6 if kind in ('вокзал', 'больница') else 0.15) else 0
            base = (60 + shift
                    + k_tr * 75 * math.log(traffic / 300)
                    + 6 * offices
                    - 18 * competitors
                    - 1.2 * rent_k
                    + kind_eff[kind]
                    + 20 * hours24)
            profit = round(base + rnd.gauss(0, noise))
            rows.append([f'S-{n:05d}', city, kind, traffic, offices, competitors, rent_k, hours24, profit])
    with open(OUT / 'sites.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['site_id', 'city', 'place', 'traffic', 'offices', 'competitors', 'rent_k', 'hours24', 'profit_k'])
        w.writerows(rows)
    print(f'sites.csv: {len(rows)}')


# ---------- глава 9: анкеты участников семейной программы ----------

def gen_chapter9(rnd: random.Random) -> None:
    """family_members.csv: анкеты участников семейной программы лояльности.
    Персональные данные (пол, возраст, доход, размер семьи) нужно передать подрядчику так,
    чтобы их нельзя было прочитать, а модель трат работала так же."""
    import math
    rows = []
    for i in range(5000):
        gender = 1 if rnd.random() < 0.55 else 0          # 1 — женщина
        age = int(min(70, max(18, rnd.gauss(36, 10))))
        income = int(round(max(25, math.exp(rnd.gauss(math.log(70 + 1.2 * (age - 18)), 0.35))), 0))
        family = min(6, max(1, int(rnd.gauss(2.6, 1.1) + 0.5)))
        spend = round(max(0, 4 + 0.09 * income + 3.2 * family - 0.08 * age + 2.0 * gender + rnd.gauss(0, 6)), 1)
        rows.append([f'F-{30001 + i}', gender, age, income, family, spend])
    with open(OUT / 'family_members.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['member_id', 'gender', 'age', 'income_k', 'family_size', 'spend_k'])
        w.writerows(rows)
    print(f'family_members.csv: {len(rows)}')


# ---------- глава 10: дневная выручка кофеен ----------

def gen_chapter10(rnd: random.Random) -> None:
    """daily_sales.csv: выручка шести кофеен по дням за 2024–2025.
    Нелинейности и взаимодействия: погода по-разному влияет на уличные кофейни и кофейни в ТЦ,
    жара переключает гостей на холодные напитки, акции сильнее работают в будни."""
    import math
    shops = {  # id: (город, формат, базовая выручка тыс. ₽)
        'PRM-1': ('Пермь', 'улица', 62), 'PRM-2': ('Пермь', 'ТЦ', 48),
        'KZN-1': ('Казань', 'улица', 75), 'KZN-2': ('Казань', 'бизнес-центр', 55),
        'TMN-1': ('Тюмень', 'ТЦ', 50), 'UFA-1': ('Уфа', 'бизнес-центр', 45),
    }
    holidays = {(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 23), (3, 8), (5, 1), (5, 9), (6, 12), (11, 4)}
    rows = []
    day = dt.date(2024, 1, 1)
    temp_noise = {c: 0.0 for c in ('Пермь', 'Казань', 'Тюмень', 'Уфа')}
    while day <= dt.date(2025, 12, 31):
        doy = day.timetuple().tm_yday
        for c in temp_noise:
            temp_noise[c] = 0.7 * temp_noise[c] + rnd.gauss(0, 3)
        rain_city = {c: (1 if rnd.random() < 0.28 else 0) for c in temp_noise}
        for sid, (city, fmt, base) in shops.items():
            t = -2 + 17 * math.sin(2 * math.pi * (doy - 110) / 365) + temp_noise[city] - (3 if city == 'Тюмень' else 0)
            t = round(t, 1)
            rain = rain_city[city]
            wd = day.weekday()
            hol = 1 if (day.month, day.day) in holidays else 0
            promo = 1 if rnd.random() < 0.12 else 0
            mult = 1.0
            if fmt == 'бизнес-центр':
                mult *= 0.35 if (wd >= 5 or hol) else 1.12
            elif fmt == 'ТЦ':
                mult *= 1.3 if (wd >= 5 or hol) else 0.95
                mult *= 1.12 if rain else 1.0                 # в дождь в ТЦ идут больше
            else:
                mult *= 1.1 if wd >= 5 else 1.0
                mult *= 0.78 if rain else 1.0                 # уличную в дождь обходят
                mult *= 1 + 0.012 * max(0, t - 5) - 0.01 * max(0, -t - 10)   # тепло — прогулки
            if t > 24:
                mult *= 1 + 0.02 * (t - 24) * (1.5 if fmt != 'бизнес-центр' else 0.5)   # холодные напитки
            if promo:
                mult *= 1.25 if wd < 5 else 1.07
            if day.month == 12 and day.day >= 15:
                mult *= 1.15
            growth = 1 + 0.08 * ((day - dt.date(2024, 1, 1)).days / 365)
            rev = base * mult * growth * math.exp(rnd.gauss(0, 0.08))
            rows.append([day.isoformat(), sid, city, fmt, t, rain, hol, promo, round(rev, 1)])
        day += dt.timedelta(days=1)
    with open(OUT / 'daily_sales.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['date', 'shop_id', 'city', 'format', 'temp', 'rain', 'holiday', 'promo', 'revenue_k'])
        w.writerows(rows)
    print(f'daily_sales.csv: {len(rows)}')


# ---------- глава 12: заказы через приложение по часам ----------

def gen_chapter12(rnd: random.Random) -> None:
    """app_orders.csv: число заказов через приложение по часам, март — август 2026.
    Рост аудитории приложения (тренд), суточный профиль с утренним и вечерним пиком,
    недельный профиль (в выходные утро позже), шум с автокорреляцией, акции и сбой приложения."""
    import math
    hour_prof = [0.6, 0.3, 0.2, 0.15, 0.2, 0.5, 1.6, 4.2, 6.5, 5.0, 3.8, 3.6, 5.2, 5.6, 4.0,
                 3.4, 3.6, 4.4, 5.8, 5.2, 3.6, 2.4, 1.6, 1.0]
    wkend_prof = [0.9, 0.5, 0.3, 0.2, 0.2, 0.3, 0.6, 1.2, 2.6, 4.4, 5.6, 5.8, 5.6, 5.2, 4.8,
                  4.6, 4.6, 4.8, 5.0, 4.6, 3.8, 2.8, 2.0, 1.3]
    rows = []
    t0 = dt.datetime(2026, 3, 1)
    ar = 0.0
    promo_days = {dt.date(2026, 4, 17), dt.date(2026, 5, 22), dt.date(2026, 6, 19), dt.date(2026, 7, 24), dt.date(2026, 8, 21)}
    outage = (dt.datetime(2026, 6, 3, 12), dt.datetime(2026, 6, 3, 17))
    for i in range(184 * 24):
        ts = t0 + dt.timedelta(hours=i)
        days = i / 24
        trend = 9 * (1 + 0.55 * days / 184)            # аудитория растёт
        season = 1.0
        prof = (wkend_prof if ts.weekday() >= 5 else hour_prof)[ts.hour] / 4
        ar = 0.6 * ar + rnd.gauss(0, 0.12)
        lam = trend * season * prof * math.exp(ar)
        if ts.date() in promo_days and 10 <= ts.hour <= 20:
            lam *= 1.6
        if outage[0] <= ts < outage[1]:
            lam *= 0.05
        # пуассоновский шум (через сумму экспонент)
        k, s = 0, rnd.expovariate(1.0)
        while s < lam:
            k += 1
            s += rnd.expovariate(1.0)
        rows.append([ts.strftime('%Y-%m-%d %H:%M'), k])
    with open(OUT / 'app_orders.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['datetime', 'orders'])
        w.writerows(rows)
    print(f'app_orders.csv: {len(rows)}')


# ---------- глава 13: тексты отзывов ----------

def gen_chapter13(rnd: random.Random) -> None:
    """reviews_text.csv: отзывы гостей в приложении с оценкой 1–5 и основной темой.
    Тексты собраны из фраз-шаблонов с вариациями: отрицания («не понравился»), смешанные отзывы
    («кофе отличный, но…»), опечатки, около 6 % оценок не совпадают с текстом (промах пальцем)."""
    topics = ['кофе', 'еда', 'обслуживание', 'доставка', 'цена', 'атмосфера']
    pos = {
        'кофе': ['кофе очень вкусный', 'отличный капучино', 'латте просто супер', 'раф вкуснейший', 'кофе всегда свежий и ароматный',
                 'лучший флэт уайт в городе', 'зерно хорошей обжарки, чувствуется', 'капучино с идеальной пенкой'],
        'еда': ['круассаны свежие', 'сырники как у бабушки', 'вкусные десерты', 'сэндвич сытный и свежий', 'выпечка тёплая и вкусная',
                'чизкейк просто тает', 'завтраки отличные'],
        'обслуживание': ['бариста очень приветливые', 'обслужили быстро', 'персонал вежливый', 'девушка на кассе помогла выбрать',
                         'бариста запомнил мой заказ', 'сотрудники всегда улыбаются', 'приготовили быстро даже в очередь'],
        'доставка': ['доставили быстро', 'курьер приехал раньше обещанного', 'кофе привезли горячим', 'доставка точно ко времени',
                     'курьер вежливый', 'всё привезли аккуратно, ничего не пролилось'],
        'цена': ['цены адекватные', 'недорого для такого качества', 'хорошие скидки по карте', 'бонусы реально копятся',
                 'цена соответствует качеству', 'приятные акции в приложении'],
        'атмосфера': ['уютно и спокойно', 'приятная музыка', 'удобно работать с ноутбуком', 'чисто и светло', 'красивый интерьер',
                      'тихо, можно посидеть с книгой'],
    }
    neg = {
        'кофе': ['кофе горький', 'капучино не понравился', 'латте был холодный', 'кофе пережжённый', 'раф слишком сладкий',
                 'кофе водянистый, вкуса нет', 'молоко было кислое'],
        'еда': ['круассан чёрствый', 'сэндвич заветренный', 'десерт несвежий', 'сырники пересушены', 'выпечка вчерашняя',
                'в салате попался волос'],
        'обслуживание': ['бариста грубил', 'ждали заказ 20 минут', 'перепутали заказ', 'персонал не обращает внимания',
                         'на кассе нахамили', 'никто не поздоровался', 'долго не могли принять оплату'],
        'доставка': ['доставка опоздала на час', 'курьер привёз холодный кофе', 'кофе пролился в пакете', 'заказ привезли не тот',
                     'курьер не мог найти адрес', 'доставили через полтора часа', 'привезли без крышки'],
        'цена': ['слишком дорого', 'цены подняли, а качество хуже', 'за такие деньги ожидала большего', 'бонусы не начислились',
                 'дороговато для такого кофе', 'акция в приложении не сработала'],
        'атмосфера': ['грязные столы', 'очень шумно', 'душно и тесно', 'негде сесть', 'громкая музыка мешает', 'в туалете грязно'],
    }
    openers = ['', '', '', 'Были сегодня. ', 'Заказывала через приложение. ', 'Хожу сюда давно. ', 'Первый раз у вас. ',
               'Зашёл утром перед работой. ', 'Брали с собой. ']
    closers_pos = ['', '', ' Спасибо!', ' Рекомендую.', ' Приду ещё.', ' Всем советую.', ' 10 из 10.']
    closers_neg = ['', '', ' Больше не приду.', ' Разочарована.', ' Обидно.', ' Исправьтесь.', ' Не советую.']

    def typo(text):
        if rnd.random() < 0.15 and len(text) > 10:
            i = rnd.randrange(1, len(text) - 1)
            return text[:i] + text[i + 1:]
        return text

    rows = []
    for i in range(2400):
        topic = rnd.choices(topics, weights=[30, 15, 20, 15, 10, 10])[0]
        kind = rnd.choices(['pos', 'neg', 'mixed'], weights=[55, 30, 15])[0]
        other = rnd.choice([t for t in topics if t != topic])
        if kind == 'pos':
            parts = [rnd.choice(pos[topic])]
            if rnd.random() < 0.4:
                parts.append(rnd.choice(pos[other]))
            text = rnd.choice(openers) + ', '.join(parts).capitalize() + '.' + rnd.choice(closers_pos)
            rating = rnd.choice([5, 5, 5, 4])
        elif kind == 'neg':
            parts = [rnd.choice(neg[topic])]
            if rnd.random() < 0.4:
                parts.append(rnd.choice(neg[other]))
            text = rnd.choice(openers) + ', '.join(parts).capitalize() + '.' + rnd.choice(closers_neg)
            rating = rnd.choice([1, 1, 2, 2, 3])
        else:   # хвалят другое, но жалуются на основную тему
            text = rnd.choice(openers) + (rnd.choice(pos[other]) + ', но ' + rnd.choice(neg[topic])).capitalize() + '.'
            rating = rnd.choice([2, 3, 3])
        text = typo(text)
        if rnd.random() < 0.06:                       # промах пальцем
            rating = 6 - rating
        rows.append([f'R-{40001 + i}', rnd.choice(['PRM-1', 'PRM-2', 'KZN-1', 'KZN-2', 'TMN-1', 'UFA-1']), text, rating, topic])
    with open(OUT / 'reviews_text.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['review_id', 'shop_id', 'text', 'rating', 'topic'])
        w.writerows(rows)
    print(f'reviews_text.csv: {len(rows)}')

    # reviews_new.csv: отзывы без оценок и тем за сентябрь–октябрь 2026 (для проекта главы).
    # Сюжет: с 2026-10-05 KZN-2 работает с новой службой доставки — жалоб на доставку резко больше.
    # TMN-1 стабильно хуже остальных весь период (высокий уровень, но без роста).
    import datetime as _dt
    rnd2 = random.Random(13113)

    def typo2(text):
        if rnd2.random() < 0.15 and len(text) > 10:
            i = rnd2.randrange(1, len(text) - 1)
            return text[:i] + text[i + 1:]
        return text

    start = _dt.date(2026, 9, 1)
    new_rows = []
    for i in range(4800):
        d = start + _dt.timedelta(days=rnd2.randrange(61))
        shop = rnd2.choice(['PRM-1', 'PRM-2', 'KZN-1', 'KZN-2', 'TMN-1', 'UFA-1'])
        broken = shop == 'KZN-2' and d >= _dt.date(2026, 10, 5)
        tw = [30, 15, 20, 15, 10, 10] if not broken else [20, 10, 14, 42, 7, 7]
        topic = rnd2.choices(topics, weights=tw)[0]
        kw = [42, 44, 14] if shop == 'TMN-1' else [60, 26, 14]
        if broken and topic == 'доставка':
            kw = [10, 70, 20]
        kind = rnd2.choices(['pos', 'neg', 'mixed'], weights=kw)[0]
        other = rnd2.choice([t for t in topics if t != topic])
        if kind == 'pos':
            parts = [rnd2.choice(pos[topic])]
            if rnd2.random() < 0.4:
                parts.append(rnd2.choice(pos[other]))
            text = rnd2.choice(openers) + ', '.join(parts).capitalize() + '.' + rnd2.choice(closers_pos)
        elif kind == 'neg':
            parts = [rnd2.choice(neg[topic])]
            if rnd2.random() < 0.4:
                parts.append(rnd2.choice(neg[other]))
            text = rnd2.choice(openers) + ', '.join(parts).capitalize() + '.' + rnd2.choice(closers_neg)
        else:
            text = rnd2.choice(openers) + (rnd2.choice(pos[other]) + ', но ' + rnd2.choice(neg[topic])).capitalize() + '.'
        new_rows.append([d.isoformat(), shop, typo2(text)])
    new_rows.sort(key=lambda x: x[0])
    with open(OUT / 'reviews_new.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['review_id', 'date', 'shop_id', 'text'])
        w.writerows([[f'N-{50001 + i}'] + row for i, row in enumerate(new_rows)])
    print(f'reviews_new.csv: {len(new_rows)}')


# ---------- глава 14: кадры витрины ----------

CV_CLASSES = ['пусто', 'круассан', 'маффин', 'печенье']
S = 32

def _grid():
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    return yy + 0.5, xx + 0.5

def _soft(d):            # знаковое расстояние → маска 0..1 со сглаженным краем
    return 1 / (1 + np.exp(np.clip(d, -30, 30) * 2.5))

def draw(rng, cls, light=1.0, warm=0.0):
    yy, xx = _grid()
    # фон: поднос со слабым градиентом
    g = rng.uniform(-0.12, 0.12, 2)
    img = 0.78 + g[0] * (yy / S - 0.5) + g[1] * (xx / S - 0.5)
    cy, cx = S / 2 + rng.uniform(-6, 6, 2)
    sc = rng.uniform(0.7, 1.2)
    if cls == 0:             # пусто: крошки
        for _ in range(rng.integers(0, 6)):
            py, px = rng.uniform(3, S - 3, 2)
            m = _soft(np.hypot(yy - py, xx - px) - rng.uniform(0.6, 1.3))
            img = img * (1 - m) + 0.5 * m
    elif cls == 1:           # круассан: полумесяц с полосками
        r = 10 * sc
        ang = rng.uniform(0, 2 * np.pi)
        oy, ox = np.sin(ang) * r * 0.55, np.cos(ang) * r * 0.55
        d1 = np.hypot(yy - cy, xx - cx) - r
        d2 = r * 0.8 - np.hypot(yy - cy - oy, xx - cx - ox)
        m = _soft(np.maximum(d1, d2))
        theta = np.arctan2(yy - cy, xx - cx)
        tone = 0.42 + 0.08 * np.sin(theta * 9)
        img = img * (1 - m) + tone * m
    elif cls == 2:           # маффин: стакан-основание и шапка
        w, h = 8 * sc, 8 * sc
        top = cy - 1
        base = np.maximum(np.abs(xx - cx) - (w * 0.95 - (yy - top) * 0.2), np.maximum(top - yy, yy - (top + h)))
        mb = _soft(base)
        tone_b = 0.55 + 0.05 * np.sign(np.sin((xx - cx) * 1.2))
        img = img * (1 - mb) + tone_b * mb
        dome = np.hypot((xx - cx) / (w * 1.2), (yy - top) / (h * 0.8)) - 1
        md = _soft(dome * 6) * (yy <= top + 0.5)
        img = img * (1 - md) + 0.28 * md
    else:                    # печенье: круг с тёмными каплями
        r = 10 * sc
        m = _soft(np.hypot(yy - cy, xx - cx) - r)
        img = img * (1 - m) + 0.6 * m
        for _ in range(rng.integers(3, 8)):
            a, rr = rng.uniform(0, 2 * np.pi), rng.uniform(0, r * 0.75)
            py, px = cy + rr * np.sin(a), cx + rr * np.cos(a)
            mm = _soft(np.hypot(yy - py, xx - px) - rng.uniform(0.8, 1.4)) * m
            img = img * (1 - mm) + 0.25 * mm
    if rng.random() < 0.3:   # ценник или край салфетки — помеха
        y0, x0 = rng.integers(0, S - 6, 2)
        img[y0:y0 + rng.integers(3, 7), x0:x0 + rng.integers(5, 10)] = rng.uniform(0.15, 0.95)
    img = img * rng.uniform(0.8, 1.15) * light + warm
    img = img + rng.normal(0, 0.06, img.shape)
    return (np.clip(img, 0, 1) * 255).round().astype(np.uint8)


def gen_chapter14(seed: int) -> None:
    """showcase.npz: 2000 кадров ячеек витрины 32×32 (оттенки серого, uint8) при дневном свете, метки 0–3.
    showcase_day.npz: один день с камеры над витриной — 12 ячеек × кадр каждые 15 минут 07:00–22:00.
    Ячейки 0–3 — круассаны, 4–7 — маффины, 8–11 — печенье; товар раскупают, в 13:00 и 17:00 допекают.
    С 18:00 в зале включают вечерний свет: кадры темнее и ниже по контрасту (сдвиг данных для проекта)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    y = rng.choice(4, size=2000)
    X = np.stack([draw(rng, c) for c in y])
    np.savez_compressed(OUT / 'showcase.npz', X=X, y=y, classes=np.array(CV_CLASSES))

    product = np.repeat([1, 2, 3], 4)
    stock = rng.integers(3, 9, 12)
    times, slots, labels, frames = [], [], [], []
    for k in range(61):
        minutes = 7 * 60 + 15 * k
        hhmm = f'{minutes // 60:02d}:{minutes % 60:02d}'
        if hhmm in ('13:00', '17:00'):
            stock = np.where(stock == 0, rng.integers(4, 9, 12), stock)
        busy = 0.35 if hhmm < '10:00' or '12:00' <= hhmm < '14:00' else 0.2
        stock = np.maximum(stock - (rng.random(12) < busy), 0)
        evening = hhmm >= '18:00'
        for s in range(12):
            c = int(product[s]) if stock[s] > 0 else 0
            frames.append(draw(rng, c, light=0.6 if evening else 1.0, warm=0.03 if evening else 0.0))
            times.append(hhmm); slots.append(s); labels.append(c)
    np.savez_compressed(OUT / 'showcase_day.npz', X=np.stack(frames), slot=np.array(slots), time=np.array(times),
                        y=np.array(labels), classes=np.array(CV_CLASSES))
    print(f'showcase.npz: {len(X)}, showcase_day.npz: {len(frames)}')


# ---------- глава 15: журнал сервиса прогноза оттока ----------

def gen_chapter15(rnd: random.Random) -> None:
    """service_log.jsonl: журнал HTTP-сервиса модели оттока за неделю 2–8 ноября 2026, одна строка — один запрос.
    Анкеты гостей — из guests_churn.csv со случайными изменениями. Инциденты для проекта главы:
    5.11 10:00 — выкатили модель 1.1: медленнее (p95 ~130 мс против ~45);
    с 6.11 — приложение 3.2 присылает avg_check в копейках (×100), сервис отвечает 200;
    с 7.11 18:00 — сайт перестал присылать delivery_share → ошибка 500 KeyError;
    фоном ~1 % ответов 422 (отрицательные числа и пропущенные поля)."""
    with open(OUT / 'guests_churn.csv', encoding='utf-8') as f:
        guests = list(csv.DictReader(f))
    feats = ['city', 'tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check',
             'delivery_share', 'fav_category', 'promo_used', 'complaints']
    start = dt.datetime(2026, 11, 2)
    lines = []
    n = 0
    for day in range(7):
        for hour in range(7, 23):
            rate = 22 if hour in (8, 9, 13, 18, 19) else 14
            for _ in range(max(0, int(rnd.gauss(rate, 3)))):
                ts = start + dt.timedelta(days=day, hours=hour, seconds=rnd.randrange(3600))
                n += 1
                g = rnd.choice(guests)
                payload = {}
                for k in feats:
                    v = g[k]
                    if k in ('city', 'fav_category'):
                        payload[k] = v
                    elif k == 'avg_check':
                        payload[k] = None if v == '' else int(v)
                    elif k == 'delivery_share':
                        payload[k] = float(v)
                    else:
                        payload[k] = int(v)
                payload['guest_id'] = g['guest_id']
                if ts < dt.datetime(2026, 11, 6):
                    client = rnd.choices(['app 3.1', 'web'], weights=[70, 30])[0]
                else:
                    client = rnd.choices(['app 3.1', 'app 3.2', 'web'], weights=[25, 45, 30])[0]
                if client == 'app 3.2' and payload['avg_check'] is not None:
                    payload['avg_check'] *= 100
                version = '1.1' if ts >= dt.datetime(2026, 11, 5, 10) else '1.0'
                status, error = 200, ''
                r = rnd.random()
                if r < 0.006:
                    payload['visits_90d'] = -1
                    status, error = 422, 'visits_90d: ожидается число ≥ 0'
                elif r < 0.011:
                    payload.pop('tenure_months')
                    status, error = 422, 'tenure_months: обязательное поле'
                if client == 'web' and ts >= dt.datetime(2026, 11, 7, 18):
                    payload.pop('delivery_share', None)
                    if status == 200:
                        status, error = 500, "KeyError: 'delivery_share'"
                base = 28 if version == '1.0' else 85
                latency = round(base * math.exp(rnd.gauss(0, 0.28)) + (rnd.expovariate(1 / 15) if rnd.random() < 0.1 else 0), 1)
                if status != 200:
                    latency = round(latency * 0.3, 1)
                lines.append((ts, {'ts': ts.isoformat(timespec='seconds'), 'request_id': f'q-{n:06d}', 'client': client,
                                   'model_version': version, 'status': status, 'latency_ms': latency,
                                   'error': error, 'payload': payload}))
    lines.sort(key=lambda x: x[0])
    import json
    with open(OUT / 'service_log.jsonl', 'w', encoding='utf-8') as f:
        for _, rec in lines:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f'service_log.jsonl: {len(lines)}')


if __name__ == '__main__':
    main()
