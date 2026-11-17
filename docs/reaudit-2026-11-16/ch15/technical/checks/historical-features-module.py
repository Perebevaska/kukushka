"""Подготовка доступных на конец квартала данных CRM."""
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

CATEGORY = ["plan", "city", "industry"]
NUMERIC = ["employees", "has_manager", "own_machine", "tenure_days", "orders_90",
           "revenue_90", "revenue_trend", "days_since_order", "late_share_90",
           "tickets_90", "tickets_bill_90", "pay_late_last3", "overdue_now"]
FEATURES = CATEGORY + NUMERIC
DATES = {"clients": ["created_at"], "contracts": ["start_date", "end_date"],
         "orders": ["order_date"], "tickets": ["created_at"], "invoices": ["due_date", "paid_date"]}


def read_tables(database):
    path = Path(database).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
        return {name: pd.read_sql(f'SELECT * FROM "{name}"', conn, parse_dates=dates)
                for name, dates in DATES.items()}


def active_clients(tables, cutoff):
    date = pd.Timestamp(cutoff)
    clients = tables["clients"].query("is_test == 0")
    base = clients.merge(tables["contracts"], on="client_id", validate="one_to_one")
    active = (base.start_date <= date) & (base.end_date.isna() | (base.end_date > date))
    return base.loc[active].set_index("client_id").sort_index()


def build_target(tables, cutoff, months=3):
    date = pd.Timestamp(cutoff)
    base = active_clients(tables, date)
    if date + pd.offsets.MonthEnd(months) > tables["orders"].order_date.max():
        raise ValueError("Горизонт цели ещё не наблюдался полностью")
    return base.end_date.le(date + pd.offsets.MonthEnd(months)).astype(int).rename("churn")


def build_features(tables, cutoff):
    date = pd.Timestamp(cutoff)
    base = active_clients(tables, date)
    f = base[CATEGORY + ["employees", "has_manager", "own_machine"]].copy()
    f["industry"] = f.industry.fillna("нет данных")
    f["tenure_days"] = (date - base.start_date).dt.days
    left = date - pd.Timedelta(days=90)
    orders = tables["orders"]
    hist = orders.loc[orders.client_id.isin(f.index) & (orders.order_date <= date)
                      & (orders.status != "отменён")]
    recent = hist[hist.order_date > left]
    prior = hist[(hist.order_date <= left) & (hist.order_date > left - pd.Timedelta(days=90))]
    f["orders_90"] = recent.groupby("client_id").size()
    rev = recent.groupby("client_id").amount.sum().reindex(f.index, fill_value=0)
    prev = prior.groupby("client_id").amount.sum().reindex(f.index, fill_value=0)
    f["revenue_90"] = rev
    f["revenue_trend"] = (rev - prev) / (rev + prev + 1)
    last = hist.groupby("client_id").order_date.max().reindex(f.index)
    f["days_since_order"] = (date - last.fillna(base.start_date)).dt.days
    delivered = recent[recent.status == "доставлен"]
    f["late_share_90"] = delivered.late_min.gt(0).groupby(delivered.client_id).mean()
    tickets = tables["tickets"].drop_duplicates("ticket_id")
    tickets = tickets[(tickets.created_at <= date) & (tickets.created_at > left)]
    f["tickets_90"] = tickets.groupby("client_id").size()
    f["tickets_bill_90"] = tickets[tickets.category == "счёт"].groupby("client_id").size()
    invoices = tables["invoices"]
    known = invoices[invoices.due_date <= date].sort_values(["due_date", "invoice_id"]).copy()
    paid = known.paid_date.where(known.paid_date <= date)
    known["lag"] = (paid.fillna(date) - known.due_date).dt.days.clip(lower=0)
    f["pay_late_last3"] = known.groupby("client_id").tail(3).groupby("client_id").lag.mean()
    f["overdue_now"] = known.loc[(known.due_date < date) & paid.isna()].groupby("client_id").size()
    f[NUMERIC] = f[NUMERIC].fillna(0)
    return f[FEATURES]
