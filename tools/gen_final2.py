#!/usr/bin/env python3
"""База «Зерно для офиса» для финального проекта курса (глава 15, урок 6). Синтетика, детерминированная.

    python3 tools/gen_final2.py

Пишет site/data/office.db — SQLite, выгрузка из CRM направления B2B на 1 октября 2026 г.:

  clients   — client_id, name, city, industry, employees, created_at, is_test
  contracts — client_id, plan, has_manager, own_machine, start_date, end_date
              (end_date пусто, если договор действует или расторгнут после 30.09.2026 —
              будущих расторжений выгрузка не знает)
  orders    — order_id, client_id, order_date, items, amount, late_min, status
              («доставлен», «отменён», «возврат» с отрицательной суммой)
  tickets   — ticket_id, client_id, created_at, category, text, resolved_hours
              (часть обращений выгружена дважды — один и тот же ticket_id)
  invoices  — invoice_id, client_id, month, amount, due_date, paid_date
              (paid_date пусто — не оплачен на дату выгрузки)

История. С июня 2024 года «Зерно» возит офисам кофе, выпечку и зерно для кофемашин
по договору с ежемесячным счётом. Договор можно расторгнуть в любой момент.
Заложено для проекта:
  * уход готовится заранее: за 1–2 месяца до расторжения заказов меньше, обращений больше;
  * опоздания доставки: в Уфе с апреля 2026 новый подрядчик, доля опозданий выросла втрое;
  * подорожание тарифа «Стандарт» на 12 % с 1 мая 2026 — маленькие офисы чувствительнее;
  * у части клиентов финансовые трудности — счета оплачиваются с опозданием, потом уход;
  * персональный менеджер и своя кофемашина «Зерна» удерживают;
  * ловушки: тестовые клиенты (is_test = 1), возвраты, дубли обращений, заказы и счета
    после даты среза (утечка, если не отрезать по дате), пропуски в industry.
Все случайные величины — numpy.random.default_rng(2026).
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
rng = np.random.default_rng(2026)

EXPORT = pd.Timestamp("2026-10-01")
FIRST = pd.Timestamp("2024-06-01")
CITIES = {"Казань": 0.36, "Пермь": 0.26, "Тюмень": 0.18, "Уфа": 0.20}
INDUSTRIES = ["IT", "финансы", "производство", "торговля", "госсектор", "образование", "медицина", "услуги"]
PLANS = {"Базовый": 0.40, "Стандарт": 0.42, "Премиум": 0.18}
PRICE = {"Базовый": 260.0, "Стандарт": 300.0, "Премиум": 380.0}       # средний чек за позицию, руб.

TICKET_TEXT = {
    "доставка": [
        "Курьер опоздал почти на час, совещание прошло без кофе.",
        "Заказ привезли не к тому подъезду, искали полчаса.",
        "Снова задержка доставки, второй раз за неделю.",
        "Выпечка приехала помятой, коробку явно уронили.",
        "Курьер не дозвонился до ресепшена и уехал.",
    ],
    "качество": [
        "Круассаны были чёрствые, сотрудники недовольны.",
        "Кофе в термосах остыл к моменту доставки.",
        "В заказе перепутали молоко — нужно было овсяное.",
        "Зерно для кофемашины горчит, раньше было лучше.",
    ],
    "счёт": [
        "В счёте сумма больше, чем в заказах за месяц.",
        "Просим пересчитать счёт: часть заказа была отменена.",
        "Не пришли закрывающие документы за прошлый месяц.",
        "Нужна отсрочка оплаты счёта на две недели.",
    ],
    "оборудование": [
        "Кофемашина в переговорной показывает ошибку.",
        "Нужна чистка кофемашины, кофе стал с осадком.",
        "Сломался капучинатор, ждём мастера.",
    ],
    "другое": [
        "Хотим добавить в заказ фрукты, это возможно?",
        "Подскажите, можно ли поменять день доставки?",
        "Спасибо за быструю замену, всё отлично.",
    ],
}


def month_starts(a, b):
    return pd.date_range(a.to_period("M").to_timestamp(), b, freq="MS")


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def main():
    n = 1500
    clients, contracts, orders, tickets, invoices = [], [], [], [], []
    oid = tid = iid = 0

    # даты подключения: равномерно, с небольшим ростом к 2026 году
    span = (pd.Timestamp("2026-09-15") - FIRST).days
    created = FIRST + pd.to_timedelta(np.sort((rng.power(1.3, n) * span).astype(int)), unit="D")

    for k in range(n):
        cid = f"C{k + 1:04d}"
        city = rng.choice(list(CITIES), p=list(CITIES.values()))
        industry = rng.choice(INDUSTRIES)
        employees = int(np.clip(np.round(rng.lognormal(3.6, 0.8)), 8, 900))
        plan = rng.choice(list(PLANS), p=list(PLANS.values()))
        has_manager = int(rng.random() < sigmoid(-2.2 + 0.9 * np.log(employees / 40)))
        own_machine = int(rng.random() < (0.55 if plan == "Премиум" else 0.25))
        start = created[k] + pd.Timedelta(days=int(rng.integers(0, 10)))
        is_test = 0
        clients.append([cid, f"Офис-{k + 1:04d}", city, None if rng.random() < 0.05 else industry,
                        employees, created[k].date().isoformat(), is_test])

        health = rng.normal(0.0, 0.7)
        trouble_from = (start + pd.Timedelta(days=int(rng.integers(60, 600)))) if rng.random() < 0.12 else None
        end = None
        months = month_starts(start, EXPORT - pd.Timedelta(days=1))
        churn_month = None
        # сначала решаем, в каком месяце клиент уйдёт (по месячному риску)
        for m in months[1:]:
            ufa_bad = city == "Уфа" and m >= pd.Timestamp("2026-04-01")
            late_share = 0.20 if ufa_bad else 0.06
            hike = plan == "Стандарт" and m >= pd.Timestamp("2026-05-01")
            trouble = trouble_from is not None and m >= trouble_from
            health += rng.normal(0, 0.18) - (0.25 if ufa_bad else 0) - (0.15 if hike and employees < 40 else 0)
            logit = (-3.75 - 0.9 * health + 6.0 * (late_share - 0.06) + 1.3 * trouble
                     - 0.8 * has_manager - 0.6 * own_machine - 0.25 * np.log(employees / 40)
                     + (0.5 if hike and employees < 40 else 0.0)
                     + (0.4 if (m - start).days < 120 else 0.0))
            if rng.random() < sigmoid(logit):
                churn_month = m
                break
        if churn_month is not None:
            end = churn_month + pd.Timedelta(days=int(rng.integers(0, 27)))

        contracts.append([cid, plan, has_manager, own_machine, start.date().isoformat(),
                          end.date().isoformat() if end is not None and end < EXPORT else None])

        # заказы — по неделям от начала договора до расторжения или даты выгрузки
        last = min(end, EXPORT - pd.Timedelta(days=1)) if end is not None else EXPORT - pd.Timedelta(days=1)
        base = 0.45 + employees / 70
        weeks = pd.date_range(start, last, freq="7D")
        month_amount = {}
        month_late = {}
        for w in weeks:
            ufa_bad = city == "Уфа" and w >= pd.Timestamp("2026-04-01")
            factor = np.exp(0.4 * health)
            if end is not None:
                days_left = (end - w).days
                if days_left < 30:
                    factor *= 0.3
                elif days_left < 60:
                    factor *= 0.5
                elif days_left < 100:
                    factor *= 0.75
            if w.month == 8 or (w.month == 1 and w.day < 12):
                factor *= 0.6
            for _ in range(rng.poisson(min(base * factor, 4.0))):
                day = w + pd.Timedelta(days=int(rng.integers(0, 5)))
                if day > last:
                    continue
                items = int(rng.poisson(3 + employees / 12)) + 1
                price = PRICE[plan] * (1.12 if plan == "Стандарт" and day >= pd.Timestamp("2026-05-01") else 1.0)
                amount = round(items * price * rng.uniform(0.85, 1.15), 2)
                late = int(rng.integers(15, 95)) if rng.random() < (0.20 if ufa_bad else 0.06) else 0
                r = rng.random()
                status = "отменён" if r < 0.02 else ("возврат" if r < 0.03 else "доставлен")
                if status == "возврат":
                    amount = -round(amount * rng.uniform(0.2, 1.0), 2)
                oid += 1
                orders.append([f"O{oid:06d}", cid, day.date().isoformat(), items,
                               0.0 if status == "отменён" else amount, late, status])
                key = day.to_period("M")
                if status != "отменён":
                    month_amount[key] = month_amount.get(key, 0.0) + amount
                month_late[key] = month_late.get(key, 0) + (late > 0)

        # обращения: больше при опозданиях, перед уходом и при трудностях с оплатой
        for m in month_starts(start, last):
            key = m.to_period("M")
            pre = end is not None and 0 <= (end - m).days < 100
            trouble = trouble_from is not None and m >= trouble_from
            lam = 0.06 + 0.35 * month_late.get(key, 0) + (0.6 if pre else 0) + (0.25 if trouble else 0)
            for _ in range(rng.poisson(lam)):
                if trouble and rng.random() < 0.5:
                    cat = "счёт"
                elif month_late.get(key, 0) and rng.random() < 0.6:
                    cat = "доставка"
                else:
                    cat = rng.choice(["доставка", "качество", "счёт", "оборудование", "другое"],
                                     p=[0.25, 0.3, 0.15, 0.15, 0.15])
                day = m + pd.Timedelta(days=int(rng.integers(0, 28)))
                if day > last:
                    continue
                tid += 1
                row = [f"T{tid:05d}", cid, day.date().isoformat(), cat, rng.choice(TICKET_TEXT[cat]),
                       round(float(rng.exponential(30 if cat != "другое" else 10)), 1)]
                tickets.append(row)
                if rng.random() < 0.04:
                    tickets.append(list(row))                    # дубль выгрузки

            # счёт за месяц: выставлен 1-го числа следующего месяца, срок — 10 дней
            amount = month_amount.get(key, 0.0)
            if amount <= 0:
                continue
            issued = (m + pd.offsets.MonthBegin(1))
            if issued >= EXPORT:
                continue
            due = issued + pd.Timedelta(days=10)
            if trouble:
                paid = due + pd.Timedelta(days=int(rng.integers(8, 70)))
            else:
                paid = due - pd.Timedelta(days=int(rng.integers(0, 9))) if rng.random() < 0.93 \
                    else due + pd.Timedelta(days=int(rng.integers(1, 12)))
            iid += 1
            invoices.append([f"I{iid:06d}", cid, str(key), round(amount, 2), due.date().isoformat(),
                             paid.date().isoformat() if paid < EXPORT else None])

    # тестовые клиенты: заводили при запуске интеграции, с заказами на копейки
    for j in range(3):
        cid = f"T{j + 1:03d}"
        clients.append([cid, f"ТЕСТ интеграции {j + 1}", "Казань", None, 1, "2024-06-03", 1])
        contracts.append([cid, "Базовый", 0, 0, "2024-06-03", "2024-07-15" if j == 0 else None])
        for d in pd.date_range("2024-06-04", "2026-09-28", freq="45D"):
            oid += 1
            orders.append([f"O{oid:06d}", cid, d.date().isoformat(), 1, 1.0, 0, "доставлен"])

    cl = pd.DataFrame(clients, columns=["client_id", "name", "city", "industry", "employees", "created_at", "is_test"])
    ct = pd.DataFrame(contracts, columns=["client_id", "plan", "has_manager", "own_machine", "start_date", "end_date"])
    od = pd.DataFrame(orders, columns=["order_id", "client_id", "order_date", "items", "amount", "late_min", "status"])
    od = od.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    tk = pd.DataFrame(tickets, columns=["ticket_id", "client_id", "created_at", "category", "text", "resolved_hours"])
    tk = tk.sort_values(["created_at", "ticket_id"]).reset_index(drop=True)
    iv = pd.DataFrame(invoices, columns=["invoice_id", "client_id", "month", "amount", "due_date", "paid_date"])

    out = DATA / "office.db"
    out.unlink(missing_ok=True)
    with sqlite3.connect(out) as con:
        for name, df in [("clients", cl), ("contracts", ct), ("orders", od), ("tickets", tk), ("invoices", iv)]:
            df.to_sql(name, con, index=False)
        con.execute("VACUUM")
    con.close()
    print(f"office.db: clients {len(cl)}, orders {len(od)}, tickets {len(tk)}, invoices {len(iv)}, "
          f"{out.stat().st_size / 1e6:.1f} МБ")


if __name__ == "__main__":
    main()
