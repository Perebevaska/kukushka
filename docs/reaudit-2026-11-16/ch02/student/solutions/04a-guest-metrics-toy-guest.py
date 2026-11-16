import pandas as pd
t=pd.DataFrame({"client_id":["X","X","Y","Z","Z","Z","Z"],"amount":[200,300,500,100,150,150,200]})
g=t.groupby("client_id").agg(orders=("amount","size"),revenue=("amount","sum"))
check=t["amount"].mean()
arpu=g["revenue"].mean()
repeat=(g["orders"]>=2).mean()
