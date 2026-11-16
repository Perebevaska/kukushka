import pandas as pd
df=pd.read_csv("orders_3m.csv")
def shrink(df):
    small=df.copy()
    for c in small:
        if (pd.api.types.is_string_dtype(small[c]) or small[c].dtype==object) and small[c].nunique()/len(small)<.05:
            small[c]=small[c].astype("category")
    return small
small=shrink(df)
converted=[c for c in df if str(small[c].dtype)=="category" and str(df[c].dtype)!="category"]
saved_pct=round((1-small.memory_usage(deep=True).sum()/df.memory_usage(deep=True).sum())*100,1)
