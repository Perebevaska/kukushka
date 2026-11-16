import pandas as pd
orders=[{"city":"Пермь","drink":"Латте","amount":450},{"city":"Казань","drink":"Раф"},{"city":"Пермь","drink":"Раф","amount":610},{"city":"Уфа","drink":"Мокко","amount":480},{"city":"Казань","drink":"Латте","amount":320}]
t=pd.DataFrame(orders)
n_no_amount=t["amount"].isna().sum()
total=t["amount"].sum()
avg_check=t["amount"].mean()
