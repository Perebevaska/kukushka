import pandas as pd
df=pd.read_csv("orders_3m.csv")
oct_df = df[df["datetime"].str.startswith("2026-10")]
nov_df = df[df["datetime"].str.startswith("2026-11")]
both = pd.concat([oct_df, nov_df], ignore_index=True)
print(len(both))
