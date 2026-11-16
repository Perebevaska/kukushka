from pathlib import Path
import json
D=Path(__file__).parent
codes={
'01-resample':('p-roll','''import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
trend = daily.rolling(7).mean()
print(int(trend.isna().sum()))'''),
'02-decompose':('p-acf','''import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
lags = [1, 24, 168]
values = [s.autocorr(lag) for lag in lags]
best = lags[values.index(max(values))]
print(best)'''),
'03-features':('p-lags','''import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
df["lag_1"] = s.shift(1)
df["lag_24"] = s.shift(24)
df = df.dropna()
print(len(df))'''),
'04-forecast':('p-horizon','''import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
for k in (24, 48, 168):
    df[f"lag_{k}"] = s.shift(k)
df["roll"] = s.shift(24).rolling(24).mean()
print(list(df.columns[1:]))''')}
for lesson,(task,code) in codes.items():
    r=dict(lesson=lesson,task=task,code=code,expect='Тот же численный результат; теперь только доступные строки Parsons',Q1='Собрать предложенные строки, а не вводить произвольный код',Q2='Список строк виден в публичном условии Parsons',Q3='p-roll:6, p-acf:168, p-lags:4392, p-horizon:4 названия')
    p=D/(lesson+'.retry-parsons.input.jsonl')
    p.write_text(json.dumps(r,ensure_ascii=False)+'\n')
