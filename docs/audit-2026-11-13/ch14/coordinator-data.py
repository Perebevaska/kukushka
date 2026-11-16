"""Количественный смысл пустой ячейки: пересчёт по меткам опубликованного дня."""
from pathlib import Path
import numpy as np
import pandas as pd
p=Path(__file__).resolve().parents[3]/'site/data/showcase_day.npz'
with np.load(p) as a:
    d=pd.DataFrame({'time':a['time'],'slot':a['slot'],'empty':a['y']==0})
d['product']=d.slot.map(lambda i: ('круассан','маффин','печенье')[i//4])
counts=d.groupby(['time','product']).empty.sum().unstack()
for label,idx in [('до 13:00',counts.index<'13:00'),('11:00–13:00',(counts.index>='11:00')&(counts.index<'13:00')),('13:00–17:00',(counts.index>='13:00')&(counts.index<'17:00'))]:
    c=counts.loc[idx]
    print(label, 'ячейко-часы',c.sum().mul(.25).to_dict(),'часы без товара во всех 4 ячейках',c.eq(4).sum().mul(.25).to_dict())
