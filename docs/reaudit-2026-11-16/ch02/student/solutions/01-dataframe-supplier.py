import pandas as pd
prices=pd.read_csv("supplier_prices.csv",sep=";",encoding="cp1251",decimal=",",thousands=" ")
total=round((prices["Цена, руб."]*prices["Количество"]).sum(),2)
