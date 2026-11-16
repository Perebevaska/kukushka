import json
from pathlib import Path
root=Path(__file__).parent
rows=[]
def add(l,t,code,expect):rows.append(dict(lesson=l,task=t,code=code,expect=expect))
add('02-distributions','poisson-queue','''import pandas as pd
from scipy import stats
a = pd.read_csv("arrivals.csv")
k = a.loc[a["shop_id"] == "UFA-1", "guests"]
mean_full = k.mean()
lam = round(mean_full, 3)
ratio = round(k.var(ddof=1) / mean_full, 2)
queue_prob_full = stats.poisson.sf(3, mean_full)
p_queue = round(queue_prob_full, 4)
share_queue = round((k >= 4).mean(), 4)
per_day = round(24 * queue_prob_full, 2)
''','lambda — среднее прибытий за 5 минут; sf(3) включает 4 и более. per_day — ожидаемое число таких интервалов за 24 пятиминутки, не доля дней и не число фактических очередей.')
add('04-confidence','bootstrap','''import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299) & (d["courier"] == "вело"), "actual_min"].to_numpy()
rng = np.random.default_rng(12)
boot = np.array([np.median(rng.choice(t, size=len(t), replace=True)) for _ in range(5000)])
med = np.median(t)
lo, hi = np.percentile(boot, [2.5, 97.5])
''','Медиана и процентильный интервал рассчитаны из 5000 выборок исходного размера с возвращением. Обоснование — учебное предположение независимых однораспределённых доставок; перенос на зависимые визиты не автоматический.')
add('04-confidence','coverage-small','''import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"].to_numpy()
mu = t.mean()
rng = np.random.default_rng(13)
covered = []
for _ in range(4000):
    sample = rng.choice(t, size=8, replace=True)
    se = sample.std(ddof=1) / np.sqrt(len(sample))
    lower, upper = stats.t.interval(.95, len(sample)-1, loc=sample.mean(), scale=se)
    covered.append(lower <= mu <= upper)
coverage = round(np.mean(covered), 3)
''','Доля покрытий не обязана равняться .950: t-интервал на восьми скошенных наблюдениях может иметь другое покрытие. Выборочная дисперсия с ddof=1 и df=7.')
add('05-hypotheses','one-sided','''import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
x = ok[ok["shop_id"].isin(["TMN-1", "PRM-1"])]
late = (x["actual_min"] > x["promised_min"]).to_numpy()
grp = (x["shop_id"] == "TMN-1").to_numpy()
rng = np.random.default_rng(1)
observed = late[grp].mean() - late[~grp].mean()
diffs = []
for _ in range(5000):
    shuffled = rng.permutation(grp)
    diffs.append(late[shuffled].mean() - late[~shuffled].mean())
diffs = np.array(diffs)
k_two = np.count_nonzero(np.abs(diffs) >= abs(observed) - 1e-12)
k_one = np.count_nonzero(diffs >= observed - 1e-12)
p_two = (k_two + 1) / (5000 + 1)
p_one = (k_one + 1) / (5000 + 1)
same_verdict = bool((p_two < .05) == (p_one < .05))
''','Односторонний хвост направлен на TMN-1 чаще PRM-1, двусторонний — по модулю. Оба используют конечную MC-оценку с +1 и полную точность; ожидаю более низкое p_one, но одинаковое неотвержение при .05.')
add('05-hypotheses','perm-fn','''import numpy as np
import pandas as pd

def perm_test(a, b, n_perm=2000, seed=0):
    a, b = np.asarray(a), np.asarray(b)
    observed = a.mean() - b.mean()
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    k = 0
    for _ in range(n_perm):
        shuffled = rng.permutation(pool)
        perm_difference = shuffled[:len(a)].mean() - shuffled[len(a):].mean()
        k += abs(perm_difference) >= abs(observed) - 1e-12
    return observed, (k + 1) / (n_perm + 1)

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
auto = ok.loc[ok["courier"] == "авто", "actual_min"].to_numpy()
velo = ok.loc[ok["courier"] == "вело", "actual_min"].to_numpy()
res = perm_test(auto, velo, n_perm=2000, seed=0)
assert res == perm_test(auto, velo, n_perm=2000, seed=0)
''','Разница средних авто минус вело и двустороннее p. Ровно n_perm случайных разбиений из полного пула; конечная оценка (k+1)/(n_perm+1), не ноль при k=0. Повтор с тем же seed должен совпасть.')
add('05-hypotheses','perm-snow','''import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = (ok["actual_min"] > ok["promised_min"]).to_numpy()
snow = (ok["weather"] == "снег").to_numpy()
rng = np.random.default_rng(0)
observed = late[snow].mean() - late[~snow].mean()
diffs = []
for _ in range(3000):
    shuffled = rng.permutation(snow)
    diffs.append(late[shuffled].mean() - late[~shuffled].mean())
diffs = np.array(diffs)
k = np.count_nonzero(np.abs(diffs) >= abs(observed) - 1e-12)
p_value = (k + 1) / (3000 + 1)
''','Массив 3000 разниц и положительная конечная оценка двустороннего p. Малое p говорит о несогласии с упрощённой обменной моделью; погода общая для дня, поэтому это не причинное доказательство её влияния.')
add('07-ab','ztest','''import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
ab = pd.read_csv("ab_push.csv")
a = ab.loc[ab["group"] == "A", "ordered"]
b = ab.loc[ab["group"] == "B", "ordered"]
p_value = proportions_ztest([b.sum(), a.sum()], [len(b), len(a)])[1]
difference = b.mean() - a.mean()
se = np.sqrt(a.mean()*(1-a.mean())/len(a) + b.mean()*(1-b.mean())/len(b))
ci_lo = round((difference - 1.96*se)*100, 2)
ci_hi = round((difference + 1.96*se)*100, 2)
''','p храню без округления, что явно разрешено обновлённым условием. B-A около 2.04 п.п., интервал примерно 0.52…3.56 п.п., выше нуля, но допускает прирост меньше полезного порога 2 п.п.')
(root/'retest-final-answers.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
print('7 самостоятельных программ с expect сохранены до отправки')
