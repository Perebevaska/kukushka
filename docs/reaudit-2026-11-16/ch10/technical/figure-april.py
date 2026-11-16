"""Produce the April issue's monthly values. Run in the project root."""
import os
for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from sklearn.linear_model import LinearRegression
from threadpoolctl import threadpool_limits

sales = pd.read_csv("site/data/daily_sales.csv",parse_dates=["date"])
sales = sales.loc[sales["date"] < "2025-07-01"].sort_values(["shop_id","date"]).reset_index(drop=True)
train = sales["date"] < "2025-04-01"
X = sales.assign(weekday=sales.date.dt.weekday, month=sales.date.dt.month,
                 weekend=sales.date.dt.weekday.ge(5).astype(int),
                 day_n=(sales.date-pd.Timestamp("2024-01-01")).dt.days)
for column in ["temp","rain"]:
    climate = X.loc[train].groupby("month")[column].mean()
    X[column] = X[column].astype(float)
    X.loc[~train,column] = X.loc[~train,"month"].map(climate)
X = pd.get_dummies(X[["temp","rain","holiday","promo","weekday","month","weekend","day_n","shop_id","format"]],columns=["shop_id","format"],dtype=int)
y = sales.revenue_k
with threadpool_limits(1):
    plain = HGB(random_state=0).fit(X[train],y[train]).predict(X[~train])
    level = np.exp(LinearRegression().fit(X.loc[train,["day_n"]],np.log(y[train])).predict(X[["day_n"]]))
    features = X.drop(columns="day_n")
    adjusted = HGB(random_state=0).fit(features[train], y[train]/level[train]).predict(features[~train])*level[~train]
val=sales[~train].assign(fact=y[~train],plain=plain,trend=adjusted)
print(json.dumps(val.groupby(val.date.dt.strftime("%Y-%m"))[["fact","plain","trend"]].mean().to_dict("index"),indent=2))
