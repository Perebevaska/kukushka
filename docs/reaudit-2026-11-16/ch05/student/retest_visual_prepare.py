import json
from pathlib import Path
root=Path(__file__).parent
rows=[
{
 'lesson':'04-confidence','task':'errorbars',
 'expect':'Кофейни расположены по возрастанию фактической доли. Одна точка на кофейню, усы Уилсона вычислены из числа опозданий и количества доставок именно этой кофейни; yerr — расстояния от доли до границ. Ось Y подписана «доля опозданий».',
 'code':'''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
g = ok.groupby("shop_id")["late"].agg(["sum", "size", "mean"]).sort_values("mean")
lo, hi = proportion_confint(g["sum"].to_numpy(), g["size"].to_numpy(), method="wilson")
shares = g["mean"].to_numpy()
fig, ax = plt.subplots(figsize=(8, 4))
ax.errorbar(g.index, shares, yerr=np.array([shares - lo, hi - shares]), fmt="o", capsize=4)
ax.set_ylabel("доля опозданий")
ax.set_xlabel("кофейня")
ax.set_title("Доли опозданий по кофейням с 95%-ми интервалами Уилсона")
fig.tight_layout()
'''
},
{
 'lesson':'09-project','task':'chart',
 'expect':'Оба графика используют явный порядок B, A: подписи оси, высоты, подписи значений и границы Уилсона следуют одному reindex. Слева доли опозданий среди заказов, справа конверсия среди всех сессий зоны <2 км. Высоты и расстояния yerr умножены на 100, подписи с одним знаком, заголовки содержат выводы.',
 'code':'''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

ab = pd.read_csv("ab_promise.csv", parse_dates=["ts"])
orders = ab[ab["ordered"] == 1]
order = ["B", "A"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
plots = [
    (axes[0], orders, "late", "Новое обещание: доля опозданий ниже"),
    (axes[1], ab[ab["distance_km"] < 2], "ordered", "Ближняя зона: конверсия снизилась")
]
for ax, data, metric, title in plots:
    g = data.groupby("group")[metric].agg(["sum", "size", "mean"]).reindex(order)
    shares = g["mean"].to_numpy()
    lo, hi = proportion_confint(g["sum"].to_numpy(), g["size"].to_numpy(), method="wilson")
    yerr = np.array([shares - lo, hi - shares]) * 100
    bars = ax.bar(order, shares * 100, yerr=yerr, capsize=5)
    ax.bar_label(bars, labels=[f"{value * 100:.1f}" for value in shares])
    ax.set_xlabel("группа")
    ax.set_ylabel("%")
    ax.set_title(title)
fig.tight_layout()
'''
}]
(root/'retest-visual-answers.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
print('Подготовлены два ответа с expect. Отправка не выполнялась.')
