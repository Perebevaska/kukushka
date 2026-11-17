## task: profit | Шаг 6. Список звонков в рублях | plus

На тесте посчитаны вероятности ухода `test["p"]` (предоставленная для этой самостоятельной карточки модель). Для каждого клиента: месячная выручка `R = revenue_90 / 3`, ожидаемая прибыль звонка `exp = p · 0.5 · 0.35 · 12 · R − 1500 − 0.2 · R`. Список звонков — клиенты с `exp > 0` по убыванию неокруглённой `exp`, при равенстве — по возрастанию `client_id`, не больше 150. Посчитайте **сценарный результат на наблюдаемых уходах** выбранного списка (в формуле вместо `p` — настоящий `churn`): `profit_model` (целые рубли), `n_calls` и `caught` — сколько из списка имеют наблюдаемую метку ухода. Для сравнения — `profit_rule` (150 клиентов с наименьшим `revenue_trend`, при равенстве — с меньшим `client_id`) и `profit_all` (позвонить всем).

Сохраните позиции выбранных строк таблицы `test` в `calls`. Можно взять более короткую очередь с положительной ожидаемой прибылью и обосновать её размер. Для допущений 30 %, 50 % и 70 % постройте `sensitivity` с индексом `0.3, 0.5, 0.7`. Колонки: `fixed_profit` — рубли для исходной очереди, `reselected_n` — число звонков после нового отбора при лимите 150 (та же сортировка: ожидаемая польза по убыванию, затем `client_id` по возрастанию), `reselected_profit` — рубли для нового списка. При оценке используйте наблюдаемые метки ухода и явно укажите допущение о доле спасённых.

### setup
```python
import sqlite3
import numpy as np
import pandas as pd
_con = sqlite3.connect("office.db")
clients = pd.read_sql("SELECT * FROM clients", _con)
contracts = pd.read_sql("SELECT * FROM contracts", _con, parse_dates=["start_date", "end_date"])
orders = pd.read_sql("SELECT * FROM orders", _con, parse_dates=["order_date"])
tickets = pd.read_sql("SELECT * FROM tickets", _con, parse_dates=["created_at"]).drop_duplicates("ticket_id")
invoices = pd.read_sql("SELECT * FROM invoices", _con, parse_dates=["due_date", "paid_date"])
_con.close()
base = clients[clients["is_test"] == 0].merge(contracts, on="client_id")

def active_at(cutoff):
    c = pd.Timestamp(cutoff)
    return base[(base["start_date"] <= c) & (base["end_date"].isna() | (base["end_date"] > c))]

def build_target(cutoff, months=3):
    c = pd.Timestamp(cutoff)
    act = active_at(c)
    if c + pd.offsets.MonthEnd(months) > pd.Timestamp('2026-09-30'):
        return pd.Series(pd.NA,index=act['client_id'].values,dtype='Int64',name='churn')
    y = act["end_date"].notna() & (act["end_date"] <= c + pd.offsets.MonthEnd(months))
    return pd.Series(y.astype(int).values, index=act["client_id"].values, name="churn")

def build_features(cutoff):
    c = pd.Timestamp(cutoff)
    act = active_at(c).set_index("client_id")
    f = act[["employees", "has_manager", "own_machine", "plan", "city"]].copy()
    f["industry"] = act["industry"].fillna("нет данных")
    f["tenure_days"] = (c - act["start_date"]).dt.days
    o = orders[(orders["order_date"] <= c) & (orders["status"] != "отменён")]
    o90 = o[o["order_date"] > c - pd.Timedelta(days=90)]
    prev = o[(o["order_date"] > c - pd.Timedelta(days=180)) & (o["order_date"] <= c - pd.Timedelta(days=90))]
    f["orders_90"] = o90.groupby("client_id").size().reindex(f.index, fill_value=0)
    f["revenue_90"] = o90.groupby("client_id")["amount"].sum().reindex(f.index, fill_value=0)
    rev_prev = prev.groupby("client_id")["amount"].sum().reindex(f.index, fill_value=0)
    den = f["revenue_90"] + rev_prev + 1
    f["revenue_trend"] = ((f["revenue_90"] - rev_prev) / den).where(den.ne(0), 0)
    last = o.groupby("client_id")["order_date"].max().reindex(f.index)
    f["days_since_order"] = (c - last).dt.days.fillna(f["tenure_days"])
    late = (o90[o90["status"] == "доставлен"]["late_min"] > 0).groupby(o90["client_id"]).mean()
    f["late_share_90"] = late.reindex(f.index).fillna(0)
    t90 = tickets[(tickets["created_at"] <= c) & (tickets["created_at"] > c - pd.Timedelta(days=90))]
    f["tickets_90"] = t90.groupby("client_id").size().reindex(f.index, fill_value=0)
    f["tickets_bill_90"] = t90[t90["category"] == "счёт"].groupby("client_id").size().reindex(f.index, fill_value=0)
    iv = invoices[invoices["due_date"] <= c].sort_values("due_date").copy()
    paid = iv["paid_date"].where(iv["paid_date"] <= c)
    iv["days_late"] = (paid.fillna(c) - iv["due_date"]).dt.days.clip(lower=0)
    iv["overdue"] = (paid.isna() & (iv["due_date"] < c)).astype(int)
    f["pay_late_last3"] = iv.groupby("client_id").tail(3).groupby("client_id")["days_late"].mean().reindex(f.index).fillna(0)
    f["overdue_now"] = iv.groupby("client_id")["overdue"].sum().reindex(f.index, fill_value=0)
    return f

def snapshot(cutoff):
    f = build_features(cutoff)
    f["churn"] = build_target(cutoff).reindex(f.index)
    f["cutoff"] = pd.Timestamp(cutoff)
    return f.reset_index()

CAT = ["plan", "city", "industry"]
NUM = ["employees", "has_manager", "own_machine", "tenure_days", "orders_90", "revenue_90", "revenue_trend",
       "days_since_order", "late_share_90", "tickets_90", "tickets_bill_90", "pay_late_last3", "overdue_now"]
train = pd.concat([snapshot(c) for c in ["2025-09-30", "2025-12-31", "2026-03-31"]], ignore_index=True)
test = snapshot("2026-06-30")
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
def _pre():
    return ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CAT), ("num", StandardScaler(), NUM)])
_m = make_pipeline(_pre(), LogisticRegression(max_iter=2000)).fit(train[CAT + NUM], train["churn"])
test["p"] = _m.predict_proba(test[CAT + NUM])[:, 1]
```

### starter
```python
# уже есть: test с колонками client_id, p (вероятность ухода), churn, revenue_90, revenue_trend
SAVE, MARGIN, MONTHS, CALL, DISCOUNT = 0.5, 0.35, 12, 1500, 0.2

R = test["revenue_90"] / 3

```

### check
```python
R0 = test['revenue_90'] / 3
real = test['churn'] * 0.5 * 0.35 * 12 * R0 - 1500 - 0.2 * R0
e = test['p'] * 0.5 * 0.35 * 12 * R0 - 1500 - 0.2 * R0
try:
    sel = need('calls')
except AssertionError:
    if not globals().get('_project_notebook') or 'base_ids' not in globals():
        raise
    _ids = pd.Index(base_ids)
    assert _ids.is_unique and _ids.isin(test.client_id).all(), 'В списке есть неизвестные или повторные ID офисов.'
    sel = test.reset_index().set_index('client_id').loc[_ids, 'index'].tolist()
assert len(sel)<=150 and len(set(sel))==len(sel) and set(sel)<=set(test.index), 'calls: не больше150 разных клиентских строк теста.'
assert (e.loc[sel]>0).all(), 'У выбранных клиентов сценарная ожидаемая выгода должна быть положительной.'
_ordered = test.loc[list(sel), ['client_id']].assign(_expected=e.loc[list(sel)].to_numpy()).sort_values(['_expected', 'client_id'], ascending=[False, True])
assert list(sel) == list(_ordered.index), 'calls: выбранные строки расположите по убыванию неокруглённой ожидаемой пользы; при равенстве — по возрастанию client_id. Более короткая положительная очередь допустима.'
assert need('n_calls') == len(sel), f'n_calls = {need("n_calls")}, а нужно {len(sel)}: клиенты с положительной ожидаемой прибылью, но не больше 150.'
assert abs(need('profit_model') - round(float(real[sel].sum()))) <= 1, f'profit_model = {need("profit_model")}. Сценарная оценка на известных уходах использует churn (0 или 1) при заданной доле удержания.'
assert need('caught') == int(test.loc[sel, 'churn'].sum()), f'caught = {need("caught")}.'
rule = test.sort_values(['revenue_trend', 'client_id']).index[:150]
assert abs(need('profit_rule') - round(float(real[rule].sum()))) <= 1, f'profit_rule = {need("profit_rule")}: 150 клиентов с наименьшим revenue_trend.'
assert abs(need('profit_all') - round(float(real.sum()))) <= 1, f'profit_all = {need("profit_all")}.'
if globals().get('_project_notebook') and 'sensitivity' not in globals() and 'fixed_money' in globals() and 'money' in globals():
    _fixed = fixed_money.set_index('удержание')
    _new = money[money['стратегия'] == 'модель'].set_index('удержание')
    _sens = pd.DataFrame({'fixed_profit': _fixed['рубли'], 'reselected_n': _new['звонки'], 'reselected_profit': _new['рубли']})
else:
    _sens = need('sensitivity',pd.DataFrame)
for save in (.3,.5,.7):
    expected=test['p']*save*.35*12*R0-1500-.2*R0
    observed=test['churn']*save*.35*12*R0-1500-.2*R0
    reselected=test.assign(expected_profit=expected).loc[expected>0].sort_values(["expected_profit", "client_id"], ascending=[False, True]).index[:150]
    assert close(_sens.loc[save,'fixed_profit'],round(float(observed.loc[sel].sum())),1), 'fixed_profit: меняется допущение при неизменном списке.'
    assert _sens.loc[save,'reselected_n']==len(reselected) and close(_sens.loc[save,'reselected_profit'],round(float(observed.loc[reselected].sum())),1), 'Переотбор меняет и список, и деньги; его результат сообщается отдельно.'

```

### hint
Две похожие формулы: ожидаемая (с `test["p"]`) — чтобы **выбрать**, сценарная на известных метках (с `test["churn"]`) — чтобы **оценить** выбор при заданной доле удержания. Для выбора добавьте рассчитанную пользу к `test`, оставьте положительные строки и сортируйте по `expected_profit` по убыванию, затем по `client_id` по возрастанию.

### hint
Правило: `test.sort_values(["revenue_trend", "client_id"]).index[:150]` — индексы 150 клиентов с самым сильным падением выручки. Прибыль группы — сумма сценарных результатов по её индексам: `real[idx].sum()`.

### hint
```python
exp = test["p"] * SAVE * MARGIN * MONTHS * R - CALL - DISCOUNT * R
real = test["churn"] * SAVE * MARGIN * MONTHS * R - CALL - DISCOUNT * R
ranked = test.assign(expected_profit=exp)
calls = ranked.loc[exp > 0].sort_values(["expected_profit", "client_id"], ascending=[False, True]).index[:150]
profit_model = round(float(real[calls].sum()))
...
```

### solution
```python
SAVE, MARGIN, MONTHS, CALL, DISCOUNT = 0.5, 0.35, 12, 1500, 0.2

R = test["revenue_90"] / 3
exp = test["p"] * SAVE * MARGIN * MONTHS * R - CALL - DISCOUNT * R
real = test["churn"] * SAVE * MARGIN * MONTHS * R - CALL - DISCOUNT * R

ranked = test.assign(expected_profit=exp)
calls = ranked.loc[exp > 0].sort_values(["expected_profit", "client_id"], ascending=[False, True]).index[:150]
n_calls = len(calls)
profit_model = round(float(real[calls].sum()))
caught = int(test.loc[calls, "churn"].sum())

rule = test.sort_values(["revenue_trend", "client_id"]).index[:150]
profit_rule = round(float(real[rule].sum()))
profit_all = round(float(real.sum()))
print(n_calls, caught, profit_model, profit_rule, profit_all)
rows=[]
for save in (.3,.5,.7):
    expected=test['p']*save*MARGIN*MONTHS*R-CALL-DISCOUNT*R
    scenario=test['churn']*save*MARGIN*MONTHS*R-CALL-DISCOUNT*R
    reselected=test.assign(expected_profit=expected).loc[expected>0].sort_values(["expected_profit", "client_id"], ascending=[False, True]).index[:150]
    rows.append(dict(save=save,fixed_profit=round(float(scenario.loc[calls].sum())),reselected_n=len(reselected),reselected_profit=round(float(scenario.loc[reselected].sum()))))
sensitivity=pd.DataFrame(rows).set_index('save')

```

### explain
При допущении об удержании половины уходящих отбор модели даёт 66 звонков и 34 наблюдавшихся ухода среди адресатов. Расчётная годовая ценность за вычетом затрат — около +260 тыс. ₽ для этой квартальной очереди. Правило по падению выручки заполняет все 150 мест и даёт около −227 тыс. ₽ при тех же допущениях. Общий лимит равен 150, фактический размер и расходы у двух очередей разные. Чтобы отдельно проверить качество ранжирования, сравните первые 66 офисов обеих очередей. Подтвердить пользу звонков для удержания позволил бы пилот с контрольной группой.

