import math
import pandas as pd

ans = pd.Series(llm_topic)
true = check["topic"]
valid = ans.isin(TOPICS)
n_invalid = int((~valid).sum())
ok = valid & (ans == true)
acc_llm = round(float(ok.mean()), 3)
recall_by_topic = ok.groupby(true).mean().round(3)
worst = recall_by_topic.idxmin()
acc = float(ok.mean())
se = math.sqrt(acc * (1 - acc) / len(true))
low, high = round(acc - 2 * se, 3), round(acc + 2 * se, 3)
clearly_better = low > 0.79
print(n_invalid, acc_llm, worst, low, high, clearly_better)
print(recall_by_topic)
acc_llm = round(float(ok[valid].mean()),3)
