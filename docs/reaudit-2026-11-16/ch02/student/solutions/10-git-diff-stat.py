diff = """diff --git a/README.md b/README.md
index 9ea5733..8a2292f 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,7 @@
 # Итоги осени
 
 Анализ продаж сети «Зерно» за сентябрь–ноябрь.
+
+## Выводы
+
+- Рост ноября: +9.6 % к октябрю.
diff --git a/report.py b/report.py
index fbaa5fc..e7ddf43 100644
--- a/report.py
+++ b/report.py
@@ -1,6 +1,13 @@
 import pandas as pd
 
 df = pd.read_csv("data/orders_3m.csv", parse_dates=["datetime"])
-df = df[df["channel"] == "доставка"]
-revenue = df["amount"].sum()
-print(revenue)
+delivery = df[df["channel"] == "доставка"]
+revenue_all = df["amount"].sum()
+revenue_delivery = delivery["amount"].sum()
+print(revenue_all, revenue_delivery)
+
+monthly = df.groupby(df["datetime"].dt.to_period("M"))["amount"].sum()
+print(monthly)
+
+card = df["client_id"].notna()
+print(df.loc[card, "amount"].mean(), df.loc[~card, "amount"].mean())"""

files=[line.split(" b/",1)[1] for line in diff.splitlines() if line.startswith("diff --git ")]
added=sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())
removed=sum(line.startswith("-") and not line.startswith("---") for line in diff.splitlines())
