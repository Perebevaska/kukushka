import pandas as pd
df=pd.read_csv("orders_3m.csv")
with pd.option_context("display.max_rows",6,"display.max_columns",None):
    print(df)
