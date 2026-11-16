import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
m=df.groupby(df["datetime"].dt.month)["amount"].sum()
growth=(m.loc[11]/m.loc[10]-1)*100
best=df.groupby("shop_id")["amount"].sum().idxmax()
conclusion=(f"**Что сделали:** разобрали {len(df)} заказов {df['shop_id'].nunique()} кофеен.\n"
    f"**Что нашли:** рост выручки ноября к октябрю — {growth:+.1f} %, лидер по выручке — {best}.\n"
    "**Что предлагаем:** проверить рост по отдельным дням и сохраняется ли эффект в декабре.")
