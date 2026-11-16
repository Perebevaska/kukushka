with open("orders_3m.csv",encoding="utf-8") as f:
    lines=f.read().splitlines()
head3=lines[:3]
n_delivery=sum("доставка" in line for line in lines)
n_seasonal_delivery=sum("доставка" in line and "Сезонный" in line for line in lines)
