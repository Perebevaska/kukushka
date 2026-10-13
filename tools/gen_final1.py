#!/usr/bin/env python3
"""База для итогового проекта главы 8 «От базы данных до рекомендаций» (синтетика,
детерминированная).

    python3 tools/gen_final1.py

Пишет в site/data/ один новый файл final1.db (SQLite), таблицы:
  shops        — кофейни сети;
  menu         — позиции меню с ценой и себестоимостью;
  guests       — гости с картой: дата регистрации, канал регистрации, домашняя
                 кофейня, год рождения (бывают пропуски и заглушка 1900);
  orders       — заказы гостей с картой за 1 марта – 31 июля 2026;
  order_items  — позиции заказов;
  app_sessions — сессии в приложении по месяцам (только у тех, кто им пользуется);
  complaints   — жалобы гостей;
  pilot        — пилот абонемента «Зерно+»: 1 июля 2026 части гостей отправили
                 предложение, части (контроль) — нет; bought — купил ли гость
                 абонемент до 14 июля.

Заложено для проекта:
  * склонность купить абонемент выше у тех, кто часто берёт кофе в будни утром,
    ходит в одну кофейню и пользуется приложением; ниже — у любителей доставки
    и у тех, кто жаловался;
  * часть склонности не видна в данных (шум), поэтому ROC-AUC моделей около 0.8;
  * в контрольной группе абонемент тоже покупают, но редко (органический спрос);
  * утечки: июльские заказы оплачены абонементом (payment = 'абонемент',
    price = 0), июльские сессии в приложении у купивших выше; признаки нужно
    считать строго до 1 июля 2026;
  * гости, не попавшие в пилот, — те, кому осенью решать, отправлять ли предложение.
Файлы других уроков этот скрипт не трогает.
"""
import datetime as dt
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data' / 'final1.db'
SEED = 2026_07_01
START = pd.Timestamp('2026-03-01')
CUTOFF = pd.Timestamp('2026-07-01')
END = pd.Timestamp('2026-08-01')          # не включая
N_GUESTS = 4800

SHOPS = [
    ('PRM-1', 'Пермь', 'Ленина', '2021-03-01', 24),
    ('PRM-2', 'Пермь', 'Компрос', '2023-06-15', 16),
    ('KZN-1', 'Казань', 'Баумана', '2022-04-01', 30),
    ('KZN-2', 'Казань', 'Кремлёвская', '2024-09-01', 18),
    ('TMN-1', 'Тюмень', 'Республики', '2023-02-01', 20),
    ('UFA-1', 'Уфа', 'Ленина', '2025-11-01', 22),
]
SHOP_W = np.array([0.22, 0.12, 0.25, 0.13, 0.15, 0.13])
MENU = [  # item_id, name, category, price, cost
    ('M01', 'Эспрессо', 'кофе', 120, 28),
    ('M02', 'Американо', 'кофе', 150, 30),
    ('M03', 'Капучино', 'кофе', 190, 45),
    ('M04', 'Латте', 'кофе', 210, 50),
    ('M05', 'Флэт уайт', 'кофе', 230, 52),
    ('M06', 'Раф', 'кофе', 260, 70),
    ('M07', 'Какао', 'не кофе', 180, 40),
    ('M08', 'Чай', 'не кофе', 120, 15),
    ('M09', 'Матча', 'не кофе', 250, 80),
    ('M10', 'Круассан', 'еда', 140, 45),
    ('M11', 'Сэндвич', 'еда', 260, 110),
    ('M12', 'Сырники', 'еда', 240, 75),
]
COFFEE = ['M01', 'M02', 'M03', 'M04', 'M05', 'M06']
COFFEE_W = np.array([0.07, 0.2, 0.28, 0.25, 0.12, 0.08])
OTHER = ['M07', 'M08', 'M09']
OTHER_W = np.array([0.35, 0.45, 0.2])
FOOD = ['M10', 'M11', 'M12']
FOOD_W = np.array([0.5, 0.25, 0.25])
PRICE = {m[0]: m[3] for m in MENU}


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def make_guests(rng):
    n = N_GUESTS
    reg_days = rng.integers(0, (pd.Timestamp('2026-06-20') - pd.Timestamp('2025-03-01')).days, n)
    reg = pd.Timestamp('2025-03-01') + pd.to_timedelta(reg_days, 'D')
    source = np.where(rng.random(n) < 0.42, 'приложение', 'касса')
    home = rng.choice([s[0] for s in SHOPS], n, p=SHOP_W)
    birth = rng.normal(1990, 11, n).round().clip(1950, 2008)
    birth = np.where(rng.random(n) < 0.08, np.nan, birth)
    birth = np.where(rng.random(n) < 0.012, 1900, birth)
    g = pd.DataFrame({'guest_id': [f'F{i:05d}' for i in range(1, n + 1)],
                      'reg_date': reg.strftime('%Y-%m-%d'), 'source': source,
                      'home_shop_id': home, 'birth_year': birth})
    # скрытые привычки гостя
    app = (source == 'приложение') | (rng.random(n) < 0.18)
    g['_app'] = app
    g['_freq'] = rng.lognormal(np.log(0.4), 0.75, n)            # заказов в неделю
    g['_morning'] = rng.beta(1.6, 2.4, n)                        # доля утренних будних
    g['_coffee'] = rng.beta(4.0, 1.6, n)                         # первая позиция — кофе
    g['_delivery'] = np.where(rng.random(n) < 0.35, rng.beta(1.5, 3, n), 0.0)
    g['_loyal'] = rng.beta(4, 1.8, n)                            # доля визитов в домашнюю
    g['_food'] = rng.beta(1.5, 4, n)
    g['_stop'] = np.where(rng.random(n) < 0.22, rng.uniform(0, 1, n), 2.0)  # доля периода до ухода
    g['_sess'] = np.where(app, rng.lognormal(np.log(6), 0.8, n), 0.0)       # сессий в месяц
    g['_complain'] = rng.random(n) < 0.06
    return g


def gen_orders(rng, g, start, end, rate_mult=None, sub_from=None):
    """Заказы гостей в окне [start, end). rate_mult — множитель частоты по гостю,
    sub_from — дата, с которой кофе оплачивается абонементом (NaT — нет абонемента)."""
    days = (end - start).days
    reg = pd.to_datetime(g['reg_date']).values
    first = np.maximum(reg, np.datetime64(start))
    active_days = ((np.datetime64(end) - first) / np.timedelta64(1, 'D')).clip(0)
    stop_day = np.where(g['_stop'] < 1, g['_stop'] * 153, 1e9)       # 153 дня с 1 марта
    offs = ((np.datetime64(start) - np.datetime64(START)) / np.timedelta64(1, 'D'))
    rate = g['_freq'].values / 7 * (rate_mult if rate_mult is not None else 1.0)
    n_ord = rng.poisson(rate * active_days)
    rows = []
    shops = np.array([s[0] for s in SHOPS])
    for i in np.nonzero(n_ord)[0]:
        k = n_ord[i]
        fd = (first[i] - np.datetime64(start)) / np.timedelta64(1, 'D')
        d = rng.uniform(fd, days, k)
        d = d[d + offs < stop_day[i]]
        if len(d) == 0:
            continue
        k = len(d)
        day = np.floor(d).astype(int)
        date = np.datetime64(start) + day.astype('timedelta64[D]')
        wd = ((date.astype('datetime64[D]').view('int64') - 4) % 7)            # 0 = пн
        morning = (rng.random(k) < g['_morning'].values[i] * 1.25) & (wd < 5)
        hour = np.where(morning, rng.uniform(7.3, 10.0, k), rng.uniform(10.5, 21.5, k))
        sec = (hour * 3600).astype(int) + rng.integers(0, 60, k)
        ts = date.astype('datetime64[s]') + sec.astype('timedelta64[s]')
        deliv = rng.random(k) < g['_delivery'].values[i]
        channel = np.where(deliv, 'доставка', np.where(rng.random(k) < 0.55, 'зал', 'с собой'))
        home = rng.random(k) < g['_loyal'].values[i]
        shop = np.where(home, g['home_shop_id'].values[i], rng.choice(shops, k, p=SHOP_W))
        sub = (sub_from is not None and not pd.isna(sub_from[i]))
        for j in range(k):
            items = []
            if rng.random() < g['_coffee'].values[i]:
                items.append(rng.choice(COFFEE, p=COFFEE_W))
            else:
                items.append(rng.choice(OTHER, p=OTHER_W))
            n_food = rng.poisson(g['_food'].values[i] * 1.2 + (0.3 if deliv[j] else 0))
            items += list(rng.choice(FOOD, n_food, p=FOOD_W))
            if rng.random() < 0.15:
                items.append(rng.choice(COFFEE + OTHER, p=np.r_[COFFEE_W, OTHER_W] / 2))
            paid_sub = sub and ts[j] >= np.datetime64(sub_from[i]) and channel[j] != 'доставка'
            rows.append((g['guest_id'].values[i], shop[j], ts[j], channel[j], items, paid_sub,
                         bool(g['_app'].values[i])))
    return rows


def main():
    rng = np.random.default_rng(SEED)
    g = make_guests(rng)

    # ---- заказы до пилота (март–июнь) ----
    pre = gen_orders(rng, g, START, CUTOFF)
    pre_df = pd.DataFrame([(r[0], r[2], r[3], r[4], r[1]) for r in pre],
                          columns=['guest_id', 'ts', 'channel', 'items', 'shop_id'])

    # ---- признаки, по которым «на самом деле» решают гости ----
    pre_df['morning'] = (pre_df['ts'].dt.hour < 10) & (pre_df['ts'].dt.dayofweek < 5)
    pre_df['coffee'] = pre_df['items'].map(lambda it: it[0] in COFFEE)
    pre_df['deliv'] = pre_df['channel'] == 'доставка'
    agg = pre_df.groupby('guest_id').agg(n=('ts', 'size'), last=('ts', 'max'),
                                          morning=('morning', 'mean'), coffee=('coffee', 'mean'),
                                          deliv=('deliv', 'mean'), shops=('shop_id', 'nunique'))
    g = g.merge(agg, left_on='guest_id', right_index=True, how='left')
    g['n'] = g['n'].fillna(0)
    rec = ((CUTOFF - g['last']).dt.days).fillna(150)
    weeks = ((CUTOFF - pd.to_datetime(g['reg_date']).clip(lower=START)).dt.days / 7).clip(lower=1)
    per_week = g['n'] / weeks
    latent = rng.normal(0, 0.5, len(g))
    logit = (-4.35 + 2.4 * np.log1p(per_week * 2.2) + 2.6 * (g['morning'].fillna(0) - 0.35)
             + 3.5 * np.maximum(g['morning'].fillna(0) - 0.5, 0)
             + 2.2 * (g['coffee'].fillna(0) - 0.7) - 2.8 * g['deliv'].fillna(0)
             + 0.6 * g['_app'] + 0.3 * np.log1p(g['_sess'])
             - 0.35 * (g['shops'].fillna(1) - 1) - 1.3 * g['_complain'] - 0.02 * rec
             + latent)
    g['_logit'] = logit

    # ---- пилот ----
    eligible = g[(g['n'] > 0) & (pd.to_datetime(g['reg_date']) < pd.Timestamp('2026-06-01'))].index
    pick = rng.choice(eligible, 2400, replace=False)
    grp = np.array(['предложение'] * 1800 + ['контроль'] * 600)
    rng.shuffle(grp)
    pilot = pd.DataFrame({'guest_id': g.loc[pick, 'guest_id'].values, 'grp': grp, 'idx': pick})
    lg = g.loc[pick, '_logit'].values
    p_buy = np.where(grp == 'предложение', sigmoid(lg), sigmoid(lg - 2.3))
    bought = (rng.random(2400) < p_buy).astype(int)
    pilot['bought'] = bought
    bday = rng.integers(1, 14, 2400)
    bat = CUTOFF + pd.to_timedelta(bday, 'D') + pd.to_timedelta(rng.integers(8 * 3600, 21 * 3600, 2400), 's')
    pilot['bought_at'] = np.where(bought == 1, bat.strftime('%Y-%m-%d %H:%M:%S'), None)
    pilot['sent_at'] = np.where(grp == 'предложение', '2026-07-01 10:00:00', None)
    print('пилот:', pilot.groupby('grp')['bought'].agg(['size', 'mean']).to_dict())
    off = grp == 'предложение'
    r = pd.Series(lg[off]).rank().values
    pos = bought[off] == 1
    print('AUC «истинной» склонности:', round((r[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * (~pos).sum()), 3),
          '| разброс логита:', round(float(np.std(lg)), 2))

    # ---- заказы в июле: купившие ходят чаще и платят абонементом ----
    sub_from = pd.Series(pd.NaT, index=g.index, dtype='datetime64[ns]')
    buyers = pilot[pilot['bought'] == 1]
    sub_from.loc[buyers['idx'].values] = pd.to_datetime(buyers['bought_at'].values)
    mult = np.where(sub_from.notna(), 2.2, 1.0)
    jul = gen_orders(rng, g, CUTOFF, END, rate_mult=mult, sub_from=sub_from.values)

    # ---- таблицы orders и order_items ----
    allrows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in pre] + jul
    allrows.sort(key=lambda r: r[2])
    orders, items = [], []
    for k, (gid, shop, ts, ch, its, paid_sub, app) in enumerate(allrows, start=1):
        oid = f'Q{k:06d}'
        pay = 'абонемент' if paid_sub else ('приложение' if app and rng.random() < 0.6 else 'карта')
        total = 0
        first_cov = paid_sub
        for it in its:
            price = PRICE[it]
            if first_cov and (it in COFFEE or it in OTHER):
                price, first_cov = 0, False             # один напиток в день по абонементу
            items.append((oid, it, 1, price))
            total += price
        orders.append((oid, gid, shop, str(ts).replace('T', ' ')[:19], ch, pay, total))
    orders = pd.DataFrame(orders, columns=['order_id', 'guest_id', 'shop_id', 'ordered_at',
                                           'channel', 'payment', 'amount'])
    items = pd.DataFrame(items, columns=['order_id', 'item_id', 'qty', 'price'])
    items = items.groupby(['order_id', 'item_id', 'price'], as_index=False)['qty'].sum()[
        ['order_id', 'item_id', 'qty', 'price']]

    # ---- сессии в приложении по месяцам ----
    sess = []
    months = ['2026-03', '2026-04', '2026-05', '2026-06', '2026-07']
    for i in np.nonzero(g['_app'].values)[0]:
        reg_m = g['reg_date'].values[i][:7]
        for m in months:
            if m < reg_m:
                continue
            lam = g['_sess'].values[i]
            if g['_stop'].values[i] < 1 and months.index(m) / 5 > g['_stop'].values[i]:
                lam *= 0.2
            if m == '2026-07' and not pd.isna(sub_from.values[i]):
                lam = lam * 2.5 + 6
            s = rng.poisson(lam)
            if s > 0:
                sess.append((g['guest_id'].values[i], m, int(s)))
    sess = pd.DataFrame(sess, columns=['guest_id', 'month', 'sessions'])

    # ---- жалобы ----
    comp = []
    topics = ['долгое ожидание', 'ошибка в заказе', 'качество напитка', 'доставка', 'приложение']
    for i in np.nonzero(g['_complain'].values)[0]:
        for _ in range(1 + rng.poisson(0.3)):
            day = rng.integers(0, (END - START).days)
            comp.append((g['guest_id'].values[i],
                         (START + pd.Timedelta(days=int(day), hours=int(rng.integers(9, 21)))).strftime('%Y-%m-%d %H:%M:%S'),
                         rng.choice(topics)))
    comp = pd.DataFrame(comp, columns=['guest_id', 'created_at', 'topic']).sort_values('created_at')
    comp.insert(0, 'complaint_id', [f'C{i:04d}' for i in range(1, len(comp) + 1)])

    guests = g[['guest_id', 'reg_date', 'source', 'home_shop_id', 'birth_year']].copy()
    guests['birth_year'] = guests['birth_year'].astype('Int64')
    pilot_t = pilot[['guest_id', 'grp', 'sent_at', 'bought', 'bought_at']].rename(columns={'grp': 'group_name'})
    pilot_t = pilot_t.sort_values('guest_id').reset_index(drop=True)

    if OUT.exists():
        OUT.unlink()
    con = sqlite3.connect(OUT)
    pd.DataFrame(SHOPS, columns=['shop_id', 'city', 'name', 'opened', 'seats']).to_sql('shops', con, index=False)
    pd.DataFrame(MENU, columns=['item_id', 'name', 'category', 'price', 'cost']).to_sql('menu', con, index=False)
    guests.to_sql('guests', con, index=False)
    orders.to_sql('orders', con, index=False)
    items.to_sql('order_items', con, index=False)
    sess.to_sql('app_sessions', con, index=False)
    comp.to_sql('complaints', con, index=False)
    pilot_t.to_sql('pilot', con, index=False)
    con.commit()
    con.execute('VACUUM')
    con.close()
    for name, df in [('guests', guests), ('orders', orders), ('order_items', items),
                     ('app_sessions', sess), ('complaints', comp), ('pilot', pilot_t)]:
        print(name, df.shape)
    print(OUT, round(OUT.stat().st_size / 1e6, 2), 'МБ')


if __name__ == '__main__':
    main()
