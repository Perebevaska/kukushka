"""Own implementation from public CRM definitions. No notebook globals."""
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
CAT=['plan','city','industry']
NUM=['employees','has_manager','own_machine','tenure_days','orders_90','revenue_90','revenue_trend','days_since_order','late_share_90','tickets_90','tickets_bill_90','pay_late_last3','overdue_now']
FEATURES=CAT+NUM
EXTRACT_END=pd.Timestamp('2026-09-30')
def read_tables(path):
    path=Path(path)
    if not path.is_file():raise FileNotFoundError(path)
    with sqlite3.connect(f'file:{path.resolve()}?mode=ro',uri=True) as con:
        return {n:pd.read_sql(f'SELECT * FROM {n}',con) for n in ['clients','contracts','orders','tickets','invoices']}
def clean_tables(tables):
    t={n:f.copy() for n,f in tables.items()}
    t['clients']=t['clients'].loc[t['clients'].is_test==0].copy()
    ids=t['clients'].client_id
    for n in ['contracts','orders','tickets','invoices']:
        t[n]=t[n].loc[t[n].client_id.isin(ids)].copy()
    t['tickets']=t['tickets'].drop_duplicates('ticket_id')
    for n,cols in {'clients':['created_at'],'contracts':['start_date','end_date'],'orders':['order_date'],'tickets':['created_at'],'invoices':['due_date','paid_date']}.items():
        for col in cols:t[n][col]=pd.to_datetime(t[n][col])
    return t

def active_at(tables,cutoff):
    t=clean_tables(tables);c=pd.Timestamp(cutoff)
    base=t['clients'].merge(t['contracts'],on='client_id',suffixes=('_client','_contract'))
    return base.loc[(base.start_date<=c)&(base.end_date.isna()|(base.end_date>c))].set_index('client_id')

def build_target(tables,cutoff,months=3):
    c=pd.Timestamp(cutoff);act=active_at(tables,c)
    end=c+pd.offsets.MonthEnd(months)
    if end>EXTRACT_END:return pd.Series(pd.NA,index=act.index,dtype='Int64',name='churn')
    return (act.end_date.notna()&(act.end_date<=end)).astype(int).rename('churn')

def revenue_trend(recent, previous):
    """Net returns are retained. Exactly zero denominator maps to 0 by contract."""
    recent, previous = np.asarray(recent, dtype=float), np.asarray(previous, dtype=float)
    denominator = recent + previous + 1
    return np.divide(recent - previous, denominator,
                     out=np.zeros_like(denominator, dtype=float), where=denominator != 0)

def build_features(tables,cutoff):
    c=pd.Timestamp(cutoff)
    if c>EXTRACT_END:raise ValueError('cutoff exceeds extraction date 2026-09-30')
    t=clean_tables(tables);act=active_at(tables,c)
    f=act[['plan','city','industry','employees','has_manager','own_machine']].copy()
    f['industry']=f.industry.fillna('нет данных')
    f['tenure_days']=(c-act.start_date).dt.days
    past=t['orders'].loc[(t['orders'].order_date<=c)&(t['orders'].status!='отменён')]
    recent=past.loc[past.order_date>c-pd.Timedelta(days=90)]
    previous=past.loc[(past.order_date>c-pd.Timedelta(days=180))&(past.order_date<=c-pd.Timedelta(days=90))]
    f['orders_90']=recent.groupby('client_id').size().reindex(f.index,fill_value=0)
    f['revenue_90']=recent.groupby('client_id').amount.sum().reindex(f.index,fill_value=0)
    old=previous.groupby('client_id').amount.sum().reindex(f.index,fill_value=0)
    f['revenue_trend']=revenue_trend(f.revenue_90, old)
    last=past.groupby('client_id').order_date.max().reindex(f.index)
    f['days_since_order']=(c-last).dt.days.fillna(f.tenure_days)
    delivered=recent.loc[recent.status=='доставлен'].assign(late=lambda x:x.late_min>0)
    f['late_share_90']=delivered.groupby('client_id').late.mean().reindex(f.index,fill_value=0)
    tickets=t['tickets'].loc[(t['tickets'].created_at>c-pd.Timedelta(days=90))&(t['tickets'].created_at<=c)]
    f['tickets_90']=tickets.groupby('client_id').size().reindex(f.index,fill_value=0)
    f['tickets_bill_90']=tickets.loc[tickets.category=='счёт'].groupby('client_id').size().reindex(f.index,fill_value=0)
    inv=t['invoices'].loc[t['invoices'].due_date<=c].copy()
    paid=inv.paid_date.where(inv.paid_date<=c)
    inv['late']=(paid.fillna(c)-inv.due_date).dt.days.clip(lower=0)
    inv['overdue']=(inv.due_date<c)&paid.isna()
    last3=inv.sort_values(['due_date','invoice_id']).groupby('client_id').tail(3)
    f['pay_late_last3']=last3.groupby('client_id').late.mean().reindex(f.index,fill_value=0)
    f['overdue_now']=inv.groupby('client_id').overdue.sum().reindex(f.index,fill_value=0)
    return f[FEATURES]

def snapshot(tables,cutoff,with_target=False):
    f=build_features(tables,cutoff)
    if with_target:f=f.join(build_target(tables,cutoff))
    return f.assign(cutoff=str(cutoff)).reset_index()
