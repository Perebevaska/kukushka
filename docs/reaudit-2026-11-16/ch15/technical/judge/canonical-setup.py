import sqlite3
import numpy as np
import pandas as pd
_con = sqlite3.connect("office.db")
clients = pd.read_sql("SELECT * FROM clients", _con)
contracts = pd.read_sql("SELECT * FROM contracts", _con, parse_dates=["start_date", "end_date"])
orders = pd.read_sql("SELECT * FROM orders", _con, parse_dates=["order_date"])
tickets = pd.read_sql("SELECT * FROM tickets", _con, parse_dates=["created_at"]).drop_duplicates("ticket_id")
invoices = pd.read_sql("SELECT * FROM invoices", _con, parse_dates=["due_date", "paid_date"])
_con.close()
base = clients[clients["is_test"] == 0].merge(contracts, on="client_id")

def active_at(cutoff):
    c = pd.Timestamp(cutoff)
    return base[(base["start_date"] <= c) & (base["end_date"].isna() | (base["end_date"] > c))]

def build_target(cutoff, months=3):
    c = pd.Timestamp(cutoff)
    act = active_at(c)
    if c + pd.offsets.MonthEnd(months) > pd.Timestamp('2026-09-30'):
        return pd.Series(pd.NA,index=act['client_id'].values,dtype='Int64',name='churn')
    y = act["end_date"].notna() & (act["end_date"] <= c + pd.offsets.MonthEnd(months))
    return pd.Series(y.astype(int).values, index=act["client_id"].values, name="churn")

def build_features(cutoff):
    c = pd.Timestamp(cutoff)
    act = active_at(c).set_index("client_id")
    f = act[["employees", "has_manager", "own_machine", "plan", "city"]].copy()
    f["industry"] = act["industry"].fillna("нет данных")
    f["tenure_days"] = (c - act["start_date"]).dt.days
    o = orders[(orders["order_date"] <= c) & (orders["status"] != "отменён")]
    o90 = o[o["order_date"] > c - pd.Timedelta(days=90)]
    prev = o[(o["order_date"] > c - pd.Timedelta(days=180)) & (o["order_date"] <= c - pd.Timedelta(days=90))]
    f["orders_90"] = o90.groupby("client_id").size().reindex(f.index, fill_value=0)
    f["revenue_90"] = o90.groupby("client_id")["amount"].sum().reindex(f.index, fill_value=0)
    rev_prev = prev.groupby("client_id")["amount"].sum().reindex(f.index, fill_value=0)
    den = f["revenue_90"] + rev_prev + 1
    f["revenue_trend"] = ((f["revenue_90"] - rev_prev) / den).where(den.ne(0), 0)
    last = o.groupby("client_id")["order_date"].max().reindex(f.index)
    f["days_since_order"] = (c - last).dt.days.fillna(f["tenure_days"])
    late = (o90[o90["status"] == "доставлен"]["late_min"] > 0).groupby(o90["client_id"]).mean()
    f["late_share_90"] = late.reindex(f.index).fillna(0)
    t90 = tickets[(tickets["created_at"] <= c) & (tickets["created_at"] > c - pd.Timedelta(days=90))]
    f["tickets_90"] = t90.groupby("client_id").size().reindex(f.index, fill_value=0)
    f["tickets_bill_90"] = t90[t90["category"] == "счёт"].groupby("client_id").size().reindex(f.index, fill_value=0)
    iv = invoices[invoices["due_date"] <= c].sort_values("due_date").copy()
    paid = iv["paid_date"].where(iv["paid_date"] <= c)
    iv["days_late"] = (paid.fillna(c) - iv["due_date"]).dt.days.clip(lower=0)
    iv["overdue"] = (paid.isna() & (iv["due_date"] < c)).astype(int)
    f["pay_late_last3"] = iv.groupby("client_id").tail(3).groupby("client_id")["days_late"].mean().reindex(f.index).fillna(0)
    f["overdue_now"] = iv.groupby("client_id")["overdue"].sum().reindex(f.index, fill_value=0)
    return f

def snapshot(cutoff):
    f = build_features(cutoff)
    f["churn"] = build_target(cutoff).reindex(f.index)
    f["cutoff"] = pd.Timestamp(cutoff)
    return f.reset_index()

CAT = ["plan", "city", "industry"]
NUM = ["employees", "has_manager", "own_machine", "tenure_days", "orders_90", "revenue_90", "revenue_trend",
       "days_since_order", "late_share_90", "tickets_90", "tickets_bill_90", "pay_late_last3", "overdue_now"]
train = pd.concat([snapshot(c) for c in ["2025-09-30", "2025-12-31", "2026-03-31"]], ignore_index=True)
test = snapshot("2026-06-30")
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
def _pre():
    return ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CAT), ("num", StandardScaler(), NUM)])
_m = make_pipeline(_pre(), LogisticRegression(max_iter=2000)).fit(train[CAT + NUM], train["churn"])
test["p"] = _m.predict_proba(test[CAT + NUM])[:, 1]