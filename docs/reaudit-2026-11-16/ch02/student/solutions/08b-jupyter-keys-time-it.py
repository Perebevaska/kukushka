import timeit
import pandas as pd
df=pd.read_csv("orders_3m.csv")
t_apply=timeit.timeit(lambda:df.apply(lambda r:r["amount"]/r["qty"],axis=1),number=3)/3
t_vec=timeit.timeit(lambda:df["amount"]/df["qty"],number=3)/3
faster=t_apply/t_vec
