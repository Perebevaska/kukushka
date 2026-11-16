import pandas as pd
sizes=pd.Series(["M","S","M","L","M","S"])
cat=sizes.astype("category")
cats=cat.cat.categories.tolist()
codes=cat.cat.codes.tolist()
