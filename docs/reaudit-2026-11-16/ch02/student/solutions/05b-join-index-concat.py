import pandas as pd
df=pd.read_csv("orders_3m.csv")
sep_df=df[df["datetime"].str.startswith("2026-09")]
oct_df=df[df["datetime"].str.startswith("2026-10")]
nov_df=df[df["datetime"].str.startswith("2026-11")]
all3=pd.concat([sep_df,oct_df,nov_df],ignore_index=True)
same=len(all3)==len(df)
