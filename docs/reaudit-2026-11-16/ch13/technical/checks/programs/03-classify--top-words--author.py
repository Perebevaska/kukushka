import pandas as pd
weights = pd.Series(model[-1].coef_[0], index=model[0].get_feature_names_out())
top_bad = list(weights.sort_values(ascending=False).index[:5])
top_good = list(weights.sort_values().index[:5])
w_ne = round(weights["не"], 2)