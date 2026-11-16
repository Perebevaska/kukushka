import pandas as pd
df=pd.read_csv("orders_3m.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(menu,on="drink",how="left",validate="many_to_one")
non_coffee_share=round(full.loc[full["category"]=="не кофе","amount"].sum()/full["amount"].sum()*100,1)
