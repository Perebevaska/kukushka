import pandas as pd
df=pd.read_csv("orders_3m.csv")
report=f"**Выручка:** {df['amount'].sum()} ₽\n**Заказов:** {len(df)}\n**Средний чек:** {df['amount'].mean():.2f} ₽"
