files=["orders_3m.csv","shops.csv","menu.csv"]
lines={}
for name in files:
    with open(name,encoding="utf-8") as f:
        lines[name]=sum(1 for line in f)
n_orders=lines["orders_3m.csv"]-1
n_shops=lines["shops.csv"]-1
