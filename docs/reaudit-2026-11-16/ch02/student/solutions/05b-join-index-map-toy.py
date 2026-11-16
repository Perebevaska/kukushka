import pandas as pd
t=pd.DataFrame({"drink":["Раф","Латте","Чай","Раф"]})
price=pd.Series({"Латте":220,"Раф":260,"Какао":200})
t["price"]=t["drink"].map(price)
no_price=t["price"].isna().sum()
