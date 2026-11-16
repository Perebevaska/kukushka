import pandas as pd
import matplotlib.pyplot as plt

n["week"] = n["date"].dt.to_period("W").dt.start_time
weekly = n.groupby(["week","shop_id"])["neg"].mean().unstack()
change_date,focus_shop=weekly.diff().stack().idxmax()
jump_week = weekly[focus_shop].diff().idxmax()
sept_max = round(float(weekly.loc[weekly.index < jump_week, focus_shop].max()), 3)
print(weekly.round(2))
print(jump_week.date(), sept_max)
ax = weekly.plot(figsize=(9, 4), color="lightgray", legend=False)
weekly[focus_shop].plot(ax=ax, color="crimson", lw=3, label=focus_shop)
ax.set_ylabel("доля недовольных"); ax.legend()