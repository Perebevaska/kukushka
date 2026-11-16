by_shop = n.groupby(["shop_id", "period"])["neg"].mean().unstack()[["до", "после"]]
by_shop["рост"] = by_shop["после"] - by_shop["до"]
by_shop = by_shop.round(3).sort_values("рост", ascending=False)
worst_level = by_shop["после"].idxmax()
worst_growth = by_shop["рост"].idxmax()
print(by_shop, worst_level, worst_growth)