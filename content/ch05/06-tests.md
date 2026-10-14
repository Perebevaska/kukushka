---
title: "Статистические тесты: какой выбрать"
lead: "Перестановочный тест универсален, но медленный и требует писать цикл. Для типовых вопросов есть готовые тесты в scipy и statsmodels — одна строка вместо цикла. Разбираем шесть самых нужных, учимся выбирать тест по вопросу и типу данных — и решать, когда тест может быть односторонним (`alternative=`)."
files: [deliveries.csv]
recap:
  - "Средние двух групп: `stats.ttest_ind(a, b, equal_var=False)` — t-тест Уэлча (не требует равных дисперсий)."
  - "Среднее против числа: `stats.ttest_1samp(a, 45)`. Пары «до/после» на одних объектах: `stats.ttest_rel(after, before)`."
  - "Доли двух групп: `proportions_ztest([успехов_a, успехов_b], [n_a, n_b])` из statsmodels."
  - "Связь двух категорий: `stats.chi2_contingency(pd.crosstab(a, b))` — хи-квадрат."
  - "Скошенные данные или порядковые оценки (1–5): `stats.mannwhitneyu(a, b)` — сравнивает распределения по рангам."
  - "Односторонний тест — параметр `alternative=\"greater\"` или `\"less\"` (о первом аргументе относительно второго); в statsmodels — `\"larger\"`/`\"smaller\"`. Направление фиксируют до данных и только если обратный эффект не важен; иначе — `\"two-sided\"`."
  - "Каждый тест возвращает статистику и p-value: `res.pvalue`. К p-value всегда добавляйте размер эффекта — разницу и её интервал."
---

## Карта тестов

| Вопрос | Данные | Тест |
|---|---|---|
| Различаются ли средние двух групп? | числа, две независимые группы | t-тест Уэлча `ttest_ind(..., equal_var=False)` |
| Отличается ли среднее от заданного числа? | числа, одна группа | `ttest_1samp` |
| Изменилось ли «после» по сравнению с «до»? | пары измерений на одних объектах | парный t-тест `ttest_rel` |
| Различаются ли доли двух групп? | 0/1, две группы | z-тест для долей `proportions_ztest` |
| Связаны ли две категории? | таблица сопряжённости | хи-квадрат `chi2_contingency` |
| Различаются ли группы, если данные сильно скошены или это оценки 1–5? | числа или порядковые | Манна — Уитни `mannwhitneyu` |

Все тесты устроены одинаково: H₀ — «различий нет», результат — статистика и p-value.

::: figure test-choice
Карта тестов из таблицы выше в виде дерева вопросов: какие данные, сколько групп, одни ли это объекты, нет ли сильного перекоса.
:::

## t-тест: средние двух групп

Различается ли среднее время доставки авто- и вело-курьеров?

```python
import pandas as pd
from scipy import stats

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
auto = ok.loc[ok["courier"] == "авто", "actual_min"]
velo = ok.loc[ok["courier"] == "вело", "actual_min"]
res = stats.ttest_ind(auto, velo, equal_var=False)
print(f"среднее авто {auto.mean():.1f}, вело {velo.mean():.1f}")
print(f"t = {res.statistic:.2f}, p = {res.pvalue:.3f}")
```

`t` — **статистика теста**: разница средних, делённая на её стандартную ошибку, то есть та же идея, что z в z-тесте для двух долей. При H₀ она ложится на колокол около нуля, поэтому |t| около 2 и больше уже редкость. Здесь |t| мал, и p ≈ 0.5 — различие средних укладывается в случайность. Авто возят дальше, но быстрее; в итоге среднее время похоже.

`equal_var=False` — **t-тест Уэлча**: он не предполагает, что разброс в группах одинаковый. Это безопасный выбор по умолчанию: если дисперсии равны, он работает почти так же, как классический, а если нет — не ошибается.

::: sql
В SQL статистических тестов обычно нет — их считают в Python. Но исходные числа для них (среднее, дисперсию, количество по группам) удобно получить запросом `GROUP BY` с `AVG`, `VAR_SAMP`, `COUNT`.
:::

{{practice: welch}}

## Одна группа против числа

Доставкам с обещанием 45 минут — укладываемся ли мы в среднем в обещание?

```python
import pandas as pd
from scipy import stats

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
t45 = ok.loc[ok["promised_min"] == 45, "actual_min"]
res = stats.ttest_1samp(t45, 45)
print(f"n = {len(t45)}, среднее {t45.mean():.1f}, p = {res.pvalue:.2e}")
```

Среднее заметно меньше 45, и p крошечное (`2e-117` — это $2 \times 10^{-117}$). Для зоны 45 минут обещание с запасом.

{{practice: one-sample}}

## Парный t-тест: до и после на одних объектах

Если одни и те же объекты измерены дважды (кофейня в октябре и в ноябре), группы **не независимы**: у медленной кофейни оба числа будут выше. Парный тест сравнивает разницы внутри пар:

```python
import pandas as pd
from scipy import stats

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["month"] = ok["created"].dt.month                 # месяц — отдельным столбцом
m = ok.pivot_table(index="shop_id", columns="month", values="actual_min", aggfunc="mean")
print(m.round(1))
res = stats.ttest_rel(m[11], m[10])
print(f"в среднем по кофейням +{(m[11] - m[10]).mean():.1f} мин, p = {res.pvalue:.3f}")
```

Всего 6 пар, и p около 0.05 — на грани. По шести кофейням трудно уверенно говорить о росте.

### Разберём вместе: парный тест руками

Теперь не минуты, а **доли опозданий** — другая величина, поэтому и результат будет другим, чем у кода выше. Ноябрь против октября по шести кофейням, доли опозданий (%):

| кофейня | октябрь | ноябрь | разница |
|---|---|---|---|
| KZN-1 | 24.8 | 19.1 | −5.7 |
| KZN-2 | 29.2 | 38.6 | +9.4 |
| PRM-1 | 17.7 | 27.6 | +9.9 |
| PRM-2 | 17.0 | 16.2 | −0.8 |
| TMN-1 | 20.2 | 34.5 | +14.3 |
| UFA-1 | 19.2 | 20.7 | +1.5 |

1. Парный тест смотрит только на столбец «разница». Среднее разниц: (−5.7 + 9.4 + 9.9 − 0.8 + 14.3 + 1.5) / 6 ≈ **+4.8 п.п.**
2. Стандартное отклонение разниц ≈ **7.6** п.п. (сумма квадратов отклонений ≈ 290, делим на 5, корень).
3. SE = 7.6 / √6 ≈ **3.1**; t = 4.8 / 3.1 ≈ **1.53**.
4. При 5 степенях свободы p ≈ **0.19**.

Что получилось: в ноябре стало хуже в среднем на 5 пунктов, но кофейни разошлись в разные стороны (от −6 до +14), а их всего шесть. Такой рост неотличим от шума. Обычный t-тест на двух столбцах здесь ошибся бы иначе: он не знает, что строки — одни и те же кофейни, и смешал бы различия между кофейнями с изменением во времени.

::: figure paired-lines
Те же шесть кофеен: линия соединяет октябрь и ноябрь одной кофейни. Парный тест смотрит только на столбец разниц справа — различия между кофейнями (одни выше, другие ниже) ему не мешают.
:::

::: tip Аналогия
Чтобы понять, похудели ли участники марафона, вес каждого сравнивают с его же весом месяц назад, а не среднее «до» со средним «после». Разница между людьми — десятки килограммов, и она заглушила бы пару килограммов эффекта; разница внутри одного человека её убирает. Парный тест делает то же с кофейнями: сравнивает каждую с самой собой.
:::

```python
import numpy as np
from scipy import stats
oct_ = np.array([24.8, 29.2, 17.7, 17.0, 20.2, 19.2])
nov = np.array([19.1, 38.6, 27.6, 16.2, 34.5, 20.7])
diff = nov - oct_
print(diff.mean().round(2), diff.std(ddof=1).round(2))
print(stats.ttest_rel(nov, oct_))
```

::: quiz
Почему «октябрь против ноября» по тем же шести кофейням сравнивают парным тестом, а не обычным t-тестом двух групп?

- [x] Измерения связаны парами: парный тест смотрит на изменение внутри каждой кофейни, и различия между кофейнями ему не мешают
  > Медленная кофейня медленна в оба месяца. Разница внутри пары убирает этот постоянный сдвиг и оставляет только изменение во времени.
- [ ] Потому что кофеен мало, а парный тест работает на маленьких выборках
  > Размер выборки тут ни при чём: и обычный t-тест считается на шести значениях. Дело в том, что значения связаны попарно.
- [ ] Потому что доли опозданий не распределены нормально
  > Форма распределения влияет на выбор между t-тестом и ранговым тестом (для пар — Уилкоксона), но парный тест нужен не из-за формы, а из-за пар.
- [ ] Потому что сравниваем ровно две группы
  > Две группы сравнивает и обычный t-тест Уэлча. Парный нужен, когда группы — это одни и те же объекты.
:::

{{practice: paired}}

## z-тест для долей

Две доли — две группы «успехов» и «попыток». statsmodels принимает их списками:

```python
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
snow = ok["weather"] == "снег"
count = [ok.loc[snow, "late"].sum(), ok.loc[~snow, "late"].sum()]
nobs = [snow.sum(), (~snow).sum()]
z, p = proportions_ztest(count, nobs)
print(f"z = {z:.2f}, p = {p:.4f}")
```

p ≈ 0.001 — тот же вывод, что дал перестановочный тест в уроке «Проверка гипотез: логика и p-value», только быстрее.

{{practice: p-ztest, agree}}

## Хи-квадрат: связь категорий

Связан ли тип курьера с опозданием? Здесь не две группы, а три — и «успех» тоже категория. Тест **хи-квадрат** проверяет, отличается ли таблица сопряжённости от той, что была бы при независимости:

```python
import pandas as pd
from scipy import stats

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ct = pd.crosstab(ok["courier"], ok["late"])
chi2, p, dof, expected = stats.chi2_contingency(ct)
print(ct)
print(f"хи-квадрат = {chi2:.0f}, p = {p:.1e}")
```

`expected` — таблица, которая была бы при независимости (урок «Вероятность: частота и симуляция»: $P(A \text{ и } B) = P(A) \cdot P(B)$). Чем сильнее настоящая таблица отличается от ожидаемой, тем больше хи-квадрат и меньше p. Сама статистика — сумма по всем клеткам (наблюдаемое − ожидаемое)² / ожидаемое. `dof` — степени свободы таблицы, (строк − 1) × (столбцов − 1), здесь (3 − 1) × (2 − 1) = 2; по ним scipy переводит хи-квадрат в p, нам их считать не нужно.

{{practice: chi2}}

## Манна — Уитни: когда среднее не подходит

Оценки 1–5 — **порядковые**: «5» лучше «4», но не «на одну единицу». Среднее оценок — не совсем честная величина. Тест Манна — Уитни сравнивает группы по рангам (как Спирмен в главе 4) и не требует нормальности:

```python
import pandas as pd
from scipy import stats

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
r = ok.dropna(subset=["rating"])
res = stats.mannwhitneyu(r.loc[r["late"], "rating"], r.loc[~r["late"], "rating"])
print(f"p = {res.pvalue:.1e}")
```

Его статистика U — сколько пар «значение из первой группы больше значения из второй» (ничья считается за половину пары). Если группы одинаковы, U около половины всех пар; чем дальше от половины, тем меньше p.

Он же подходит для сильно скошенных чисел (время, деньги) с выбросами, когда среднее «тянется» хвостом.

::: predict
```python static
from scipy import stats
a = [1, 2, 3, 4, 5]
b = [1, 2, 3, 4, 5]
print(round(stats.ttest_ind(a, b).pvalue, 2))
```

- `0.0`
- `0.05`
- [x] `1.0`

Почему: группы одинаковые, разница средних ноль — данные идеально совместимы с H₀. p-value равно 1.
:::

::: warn Типичные ошибки
- **Обычный t-тест для пар.** «До» и «после» на тех же объектах — `ttest_rel`, иначе различия между объектами растворят эффект.
- **t-тест для оценок 1–5.** Порядковые данные с сильным перекосом — Манна — Уитни.
- **Хи-квадрат на долях вместо чисел.** `chi2_contingency` принимает **количества**, не проценты.
- **Знак результата.** `ttest_ind(a, b)` — статистика положительна, если среднее `a` больше; порядок аргументов важен для односторонних выводов.
:::

{{practice: mwu}}

## Односторонний тест: параметр `alternative=`

**Зачем.** Отдел доставки хочет добавлять 5 минут к обещанию в дождь — но только если в дождь доставки действительно **дольше**. Вопрос направленный: «быстрее в дождь» нас не интересует, решение в этом случае такое же, как при «разницы нет», — ничего не менять. В уроке «Проверка гипотез: логика и p-value» такой тест назывался **односторонним**, и мы считали его перемешиванием. Во всех тестах scipy он задаётся одним параметром.

::: tip Аналогия
Охранник на входе проверяет только тех, кто проходит **внутрь**: выходящие его не интересуют. Двусторонний тест — охранник, который смотрит в обе стороны: его внимание делится надвое, и каждого отдельного «нарушителя» он замечает хуже.
:::

### Игрушечный пример: одна статистика, три p-value

Пусть тест дал статистику t = 1.8 (для больших выборок её распределение при H₀ — стандартное нормальное). Посмотрим, где лежат «не менее крайние» значения:

1. **Двусторонний** (H₁: «различаются»): крайние — и больше 1.8, и меньше −1.8. Правый хвост — 0.036, левый — столько же: p = 2 × 0.036 = **0.072**.
2. **«Больше»** (H₁: «первая группа больше»): крайние — только больше 1.8: p = **0.036**.
3. **«Меньше»** (H₁: «первая группа меньше»): крайние — всё, что меньше 1.8, то есть почти весь колокол: p = **0.964**.

При α = 0.05 двусторонний тест говорит «не отвергаем», односторонний «больше» — «отвергаем». Поэтому направление и выбирают **до** данных.

::: figure alt-tails
Одна и та же статистика t = 1.8 при трёх альтернативах. Красное — значения, которые считаются «не менее крайними»; их площадь и есть p-value.
:::

```python
from scipy import stats
t = 1.8
print("двусторонний:", round(2 * stats.norm.sf(t), 3))
print("больше:      ", round(stats.norm.sf(t), 3))
print("меньше:      ", round(stats.norm.cdf(t), 3))
```

### В scipy и statsmodels

У `ttest_ind`, `ttest_1samp`, `ttest_rel` и `mannwhitneyu` есть параметр `alternative`:

| Значение | H₁ | Пример |
|---|---|---|
| `"two-sided"` (по умолчанию) | группы различаются | `ttest_ind(a, b)` |
| `"greater"` | **первый** аргумент больше второго (или больше числа) | `ttest_ind(rain, clear, alternative="greater")` |
| `"less"` | **первый** аргумент меньше второго | `ttest_1samp(t30, 30, alternative="less")` |

В statsmodels слова другие: `proportions_ztest(..., alternative="larger")` или `"smaller"`; по умолчанию `"two-sided"`.

Проверим дождь против ясной погоды в Тюмени (TMN-1):

```python
import pandas as pd
from scipy import stats

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299) & (d["shop_id"] == "TMN-1")]
rain = ok.loc[ok["weather"] == "дождь", "actual_min"]
clear = ok.loc[ok["weather"] == "ясно", "actual_min"]
print(f"дождь {rain.mean():.1f} мин (n={len(rain)}), ясно {clear.mean():.1f} мин (n={len(clear)})")
for alt in ("two-sided", "greater", "less"):
    res = stats.ttest_ind(rain, clear, equal_var=False, alternative=alt)
    print(f"{alt:>9}: p = {res.pvalue:.4f}")
```

Что здесь происходит:

- `rain` и `clear` — время доставок TMN-1 в дождь и в ясную погоду; порядок аргументов важен: `alternative` говорит о **первом** относительно второго;
- цикл трижды запускает один и тот же тест Уэлча с разными H₁;
- статистика t во всех трёх случаях одна и та же — меняется только то, какой хвост считать «крайним».

Как читать результат: в дождь доставка дольше на 3.6 минуты. Двустороннее p = 0.0527 — чуть выше 0.05; одностороннее «больше» — 0.0263, вдвое меньше; «меньше» — 0.9737: данные совсем не похожи на «в дождь быстрее». Если вопрос «дольше ли в дождь» был сформулирован до просмотра данных и обратный результат ничего бы не изменил, честный ответ — односторонний: p = 0.026, добавлять 5 минут в Тюмени оправданно.

**Когда односторонний тест допустим:**

- направление записано **до** просмотра данных и следует из бизнес-вопроса;
- результат в обратную сторону приведёт к тому же решению, что и «разницы нет»;
- эффект в обратную сторону не опасен. Если новая упаковка может **замедлить** доставку и это важно знать, нужен двусторонний тест: односторонний «быстрее» такой вред не заметит.

::: quiz
Аналитик сравнил средний чек в кофейнях с новым меню и со старым: `ttest_ind(new, old, alternative="greater")` дал p = 0.97. Что это значит?

- [x] Данные совсем не поддерживают «в новом меню чек больше»; скорее всего, он даже меньше — но этот тест такой вывод не проверяет
  > p близко к 1 при «greater» означает, что статистика ушла в другую сторону. Вопрос «стал ли чек меньше» — отдельная гипотеза, и её надо было задать заранее.
- [ ] Чек в новом меню больше с вероятностью 97 %
  > p-value — не вероятность гипотезы. Большое p при «greater» говорит как раз об обратном направлении.
- [ ] Ошибка: p-value не бывает таким большим
  > Бывает: у одностороннего теста «не в ту сторону» p близко к 1.
- [ ] Нужно взять 1 − 0.97 = 0.03 и объявить, что чек значимо меньше
  > Это смена направления после просмотра данных — та самая подгонка, которой односторонний тест опасен.
:::

::: warn Типичные ошибки
- **Направление после данных.** Посмотрели на средние, увидели «дождь дольше» и выбрали `"greater"` — p вдвое меньше честного. Направление фиксируют в плане анализа до расчётов; если его нет — `"two-sided"`.
- **Перепутали порядок аргументов.** `ttest_ind(clear, rain, alternative="greater")` проверяет «в ясную погоду дольше»; p выйдет близким к 1. Симптом: p ≈ 0.97 при явно видимом эффекте — поменяйте местами аргументы или `"greater"` на `"less"`.
- **Слова из scipy в statsmodels.** `proportions_ztest(..., alternative="greater")` выдаст `ValueError`: там `"larger"` и `"smaller"`.
- **Односторонний тест для «защитной» метрики.** Если важно поймать вред в любую сторону (выручка, жалобы), тест двусторонний.
:::

{{practice: alt-rain}}

## p-value — не размер эффекта

Маленькое p говорит «разница, скорее всего, не случайна», но не говорит, **большая** ли она. На огромных данных даже разница в 0.1 минуты будет «значимой». Поэтому вместе с p-value всегда сообщают размер эффекта:

> В снег опаздывают на 11 п.п. чаще (34 % против 23 %; 95 % ДИ разницы 4–19 п.п.; p = 0.001).

Такая фраза отвечает на три вопроса сразу: насколько, насколько точно и не случайно ли.

::: quiz
На 200 000 заказах t-тест показал p < 0.001 для разницы средних чеков 1.5 ₽. Стоит ли менять меню ради этой разницы?

- [x] Скорее нет: разница надёжно отлична от нуля, но слишком мала, чтобы ради неё что-то менять
  > На больших данных значимой становится почти любая разница. Решение принимают по размеру эффекта и его интервалу.
- [ ] Да: p < 0.001 — очень сильный эффект
  > p-value говорит о надёжности, а не о величине. 1.5 ₽ — сила эффекта, и она мала.
- [ ] Нет: тест ошибся, потому что данных слишком много
  > Тест не ошибся, просто «значимо» не значит «важно».
- [ ] Нужно уменьшить выборку, чтобы p стал честнее
  > Выбрасывать данные бессмысленно. Смотрите на эффект и интервал.
:::

{{practice: choose, report}}

## Практика

## task: welch | Пешие против вело | warmup

Сравните t-тестом Уэлча среднее время доставки пеших и вело-курьеров (1–299 минут). Сохраните `t_stat` (4 знака) и `p_value` — без округления: оно меньше 0.0001, и округление превратило бы его в ноль.

### starter
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
r = _st.ttest_ind(ok.loc[ok['courier'] == 'пеший', 'actual_min'], ok.loc[ok['courier'] == 'вело', 'actual_min'], equal_var=False)
assert close(need('t_stat'), round(r.statistic, 4)), f't_stat = {need("t_stat")}, а нужно {round(r.statistic, 4)}. Порядок групп: пешие, потом вело; equal_var=False.'
pv = float(need('p_value'))
if pv == 0:
    raise AssertionError('p_value = 0.0 — это след округления. Сохраните res.pvalue как есть, без round.')
assert abs(pv / r.pvalue - 1) < 1e-3, f'p_value = {pv}, а нужно около {r.pvalue:.2e}.'
```

### hint
Две группы: `walk` — время пеших доставок, `velo` — вело; обе — Series `actual_min` с фильтром по `courier`.

### hint
`stats.ttest_ind(walk, velo, equal_var=False)`; результат — `.statistic`, `.pvalue`.

### solution
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
walk = ok.loc[ok["courier"] == "пеший", "actual_min"]
velo = ok.loc[ok["courier"] == "вело", "actual_min"]
res = stats.ttest_ind(walk, velo, equal_var=False)
t_stat = round(res.statistic, 4)
p_value = res.pvalue
```

### explain
Пешие в среднем доставляют за 39.9 минуты, вело — за 33.1; t ≈ 9.3, p ≈ 2 · 10⁻¹⁹. В отчёт такое p пишут как «p < 0.0001», а не «p = 0.0». Разница почти 7 минут на сотнях доставок — это не может быть случайностью. Но тест не говорит почему: пешие могут возить на другие расстояния (урок «Ловушки статистики» — про такие ловушки).

## task: one-sample | Обещание 30 минут | warmup

Проверьте, укладываемся ли мы в среднем в обещание 30 минут: t-тест для одной выборки по доставкам с `promised_min == 30`. Сохраните `mean_30` (среднее, 1 знак) и `p_value` (без округления или с 4 знаками — проверка примет оба). В `beyond` — `True`, если среднее **больше** 30 и при этом p < 0.05.

### starter
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
t = ok.loc[ok['promised_min'] == 30, 'actual_min']
r = _st.ttest_1samp(t, 30)
assert close(need('mean_30'), round(t.mean(), 1)), f'mean_30 = {need("mean_30")}.'
assert close(need('p_value'), r.pvalue, 6e-5), f'p_value = {need("p_value")}, а нужно около {r.pvalue:.4f}. Тест — stats.ttest_1samp(t30, 30).'
assert need('beyond') == bool(t.mean() > 30 and r.pvalue < 0.05), 'beyond — среднее больше 30 и p < 0.05.'
```

### hint
`t30` — время доставок с обещанием 30 минут: `ok.loc[ok["promised_min"] == 30, "actual_min"]`.

### hint
`stats.ttest_1samp(t30, 30)`; `beyond = bool(t30.mean() > 30 and p < 0.05)`.

### solution
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
t30 = ok.loc[ok["promised_min"] == 30, "actual_min"]
res = stats.ttest_1samp(t30, 30)
mean_30 = round(t30.mean(), 1)
p_value = res.pvalue
beyond = bool(t30.mean() > 30 and res.pvalue < 0.05)
```

### explain
Среднее в зоне 30 минут — 30.1, на 0.1 минуты выше обещания, p ≈ 0.65: в среднем обещание выполняется впритык, значимого превышения нет, и `beyond = False`. Но «в среднем» — не то же, что «для гостя»: при среднем около 30 минут почти половина доставок (45 %) приезжает позже обещанного. Беда зоны 30 — не среднее, а доля опозданий (глава 4); средним её не увидеть.

## task: p-ztest | z-тест для долей | warmup

Соберите программу, которая сравнивает доли 30 из 200 и 45 из 210 и выводит p-value (3 знака).

### parsons
```python
from statsmodels.stats.proportion import proportions_ztest
count = [30, 45]
nobs = [200, 210]
z, p = proportions_ztest(count, nobs)
print(round(p, 3))
```

### check
```python
from statsmodels.stats.proportion import proportions_ztest as _z
assert _lines == [str(round(_z([30, 45], [200, 210])[1], 3))], f'Сейчас: {_lines}'
```

### hint
Списки «успехов» и «попыток» — до вызова теста.

### hint
`proportions_ztest` возвращает пару (статистика, p-value); печатайте второе число.

## task: paired | До и после | base

Посчитайте для каждой кофейни долю опозданий в октябре и в ноябре (таблица `m`: строки — кофейни, столбцы — месяцы 10 и 11). Проведите парный t-тест «ноябрь против октября» и сохраните `mean_change` — среднее изменение доли по кофейням в п.п. (1 знак) и `p_value` (3 знака).

### starter
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["month"] = ok["created"].dt.month

```

### check
```python
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
m = o.pivot_table(index='shop_id', columns=o['created'].dt.month, values='late', aggfunc='mean')
r = _st.ttest_rel(m[11], m[10])
assert close(need('mean_change'), round((m[11] - m[10]).mean() * 100, 1)), f'mean_change = {need("mean_change")}.'
assert close(need('p_value'), round(r.pvalue, 3)), f'p_value = {need("p_value")}, а нужно {round(r.pvalue, 3)}. Тест — ttest_rel(ноябрь, октябрь).'
```

### hint
Месяц — `ok["created"].dt.month`, его нужно добавить в `ok` до сводной таблицы.

### hint
`m = ok.pivot_table(index="shop_id", columns="month", values="late", aggfunc="mean")`; столбцы — `m[10]`, `m[11]`. Тест — `stats.ttest_rel(m[11], m[10])`.

### solution
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["month"] = ok["created"].dt.month
m = ok.pivot_table(index="shop_id", columns="month", values="late", aggfunc="mean")
mean_change = round((m[11] - m[10]).mean() * 100, 1)
p_value = round(stats.ttest_rel(m[11], m[10]).pvalue, 3)
```

### explain
Ноябрь хуже октября в среднем на 4.8 п.п., но p ≈ 0.19: на шести кофейнях с разнонаправленными изменениями это может быть шумом. Парный тест сравнивает каждую кофейню с самой собой — и всё равно не находит уверенного эффекта.

## task: chi2 | Погода и опоздания | base

Проверьте хи-квадратом, связана ли погода с опозданием. Сохраните таблицу сопряжённости в `ct` (строки — погода, столбцы — `late`), а в `chi2_p` — p-value. В `max_gap_weather` — вид погоды, где наблюдаемое число опозданий сильнее всего **превышает** ожидаемое при независимости.

### starter
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
ct = _pd.crosstab(o['weather'], o['late'])
chi2, p, dof, exp = _st.chi2_contingency(ct)
c = need('ct', _pd.DataFrame)
assert c.shape == ct.shape, 'ct — pd.crosstab(погода, late).'
assert close(need('chi2_p'), p, 6e-5), f'chi2_p = {need("chi2_p")}, а нужно около {p:.6f}.'
gap = ct[True] - exp[:, list(ct.columns).index(True)]
assert need('max_gap_weather') == gap.idxmax(), f'max_gap_weather = {need("max_gap_weather")!r}, а нужно {gap.idxmax()!r}.'
```

### hint
`chi2, p, dof, expected = stats.chi2_contingency(ct)`; `expected` — массив той же формы, что `ct`.

### hint
Опоздания — столбец `True`. Ожидаемые опоздания — `expected[:, 1]` (второй столбец). Разница — Series с индексом погоды: `ct[True] - expected[:, 1]`, и её `idxmax()`.

### solution
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ct = pd.crosstab(ok["weather"], ok["late"])
chi2, chi2_p, dof, expected = stats.chi2_contingency(ct)
gap = ct[True] - expected[:, 1]
max_gap_weather = gap.idxmax()
```

### explain
p ≈ 0.0003: погода и опоздания связаны. Сильнее всего ожидание при независимости превышено в снег — на 17 опозданий больше, чем было бы при общей частоте; в облачную погоду, наоборот, на 30 меньше. Хи-квадрат говорит «связь есть», а таблица «наблюдаемое − ожидаемое» — где она.

## task: mwu | Оценки: Манна — Уитни | base

Сравните оценки гостей при доставке в снег и в остальную погоду тестом Манна — Уитни. Сохраните `med_snow`, `med_other` — медианы оценок и `p_value` (4 знака).

### starter
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
r = ok.dropna(subset=["rating"])

```

### check
```python
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
r = ok.dropna(subset=['rating'])
s = r['weather'] == 'снег'
assert close(need('med_snow'), r.loc[s, 'rating'].median()) and close(need('med_other'), r.loc[~s, 'rating'].median()), 'Медианы оценок не совпадают.'
assert close(need('p_value'), round(_st.mannwhitneyu(r.loc[s, 'rating'], r.loc[~s, 'rating']).pvalue, 4)), f'p_value = {need("p_value")}.'
```

### hint
Оценки есть не у всех доставок: возьмите строки с непустым `rating` (`r = ok.dropna(subset=["rating"])`).

### hint
`stats.mannwhitneyu(r.loc[snow, "rating"], r.loc[~snow, "rating"]).pvalue`.

### solution
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
r = ok.dropna(subset=["rating"])
snow = r["weather"] == "снег"
med_snow = r.loc[snow, "rating"].median()
med_other = r.loc[~snow, "rating"].median()
p_value = round(stats.mannwhitneyu(r.loc[snow, "rating"], r.loc[~snow, "rating"]).pvalue, 4)
```

### explain
Медианы одинаковые — пятёрки, а p около 0.06 — на грани. Манна — Уитни сравнивает распределения целиком: в снег оценок 1–3 больше (около 16 % против 7 %), но снежных оценок всего несколько десятков, и уверенно сказать, что различие не случайно, нельзя. Медиана для оценок 1–5 — грубая мера; доля «не пятёрок» часто говорит больше.

## task: alt-rain | Дождь в Казани: дольше ли | base

План анализа записан заранее: «добавляем 5 минут к обещанию в дождь, если в дождь доставки дольше, чем в ясную погоду; α = 0.05». Проверьте его для кофейни KZN-2 тестом Уэлча (время 1–299 минут). Сохраните p-value трёх вариантов: `p_two` (двусторонний), `p_greater` (H₁: в дождь дольше) и `p_less` (H₁: в дождь быстрее) — все 4 знака. В `add_5min` — `True` или `False`: решение по тесту, который соответствует плану.

### starter
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299) & (d["shop_id"] == "KZN-2")]

```

### check
```python
import pandas as _pd
from scipy import stats as _st
_d = _pd.read_csv('deliveries.csv')
_ok = _d[_d['actual_min'].between(1, 299) & (_d['shop_id'] == 'KZN-2')]
_r = _ok.loc[_ok['weather'] == 'дождь', 'actual_min']
_c = _ok.loc[_ok['weather'] == 'ясно', 'actual_min']
_p = {a: _st.ttest_ind(_r, _c, equal_var=False, alternative=a).pvalue for a in ('two-sided', 'greater', 'less')}
assert close(need('p_two'), round(_p['two-sided'], 4)), f'p_two = {need("p_two")}. Двусторонний тест Уэлча: ttest_ind(rain, clear, equal_var=False).'
pg, pl = need('p_greater'), need('p_less')
if close(pg, round(_p['less'], 4)) and close(pl, round(_p['greater'], 4)):
    raise AssertionError('p_greater и p_less поменялись местами. alternative говорит о первом аргументе: ttest_ind(rain, clear, alternative="greater") — «в дождь больше».')
assert close(pg, round(_p['greater'], 4)), f'p_greater = {pg}. H₁ «в дождь дольше»: первый аргумент — дождь, alternative="greater".'
assert close(pl, round(_p['less'], 4)), f'p_less = {pl}. H₁ «в дождь быстрее»: alternative="less".'
assert need('add_5min') == (_p['greater'] < 0.05), 'add_5min — решение по одностороннему тесту «дольше» из плана при α = 0.05.'
```

### hint
Разделите доставки KZN-2 на дождь и ясно и трижды запустите `stats.ttest_ind(rain, clear, equal_var=False, alternative=...)`.

### hint
Значения `alternative`: `"two-sided"`, `"greater"`, `"less"`. План говорит «дольше в дождь» — это `"greater"` при первом аргументе `rain`.

### hint
`add_5min = p_greater < 0.05` — сравнивайте с α именно p из плана, а не самое маленькое из трёх.

### solution
```python
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299) & (d["shop_id"] == "KZN-2")]
rain = ok.loc[ok["weather"] == "дождь", "actual_min"]
clear = ok.loc[ok["weather"] == "ясно", "actual_min"]
p_two = round(stats.ttest_ind(rain, clear, equal_var=False).pvalue, 4)
p_greater = round(stats.ttest_ind(rain, clear, equal_var=False, alternative="greater").pvalue, 4)
p_less = round(stats.ttest_ind(rain, clear, equal_var=False, alternative="less").pvalue, 4)
add_5min = p_greater < 0.05
```

### explain
В KZN-2 в дождь доставка дольше на 3 минуты, но групп немного (50 дождливых и 106 ясных доставок). Двустороннее p = 0.108, одностороннее по плану — 0.054: тоже выше 0.05, поэтому `add_5min = False` — данных пока недостаточно, решение откладываем до новых наблюдений. Заметьте: p_greater + p_less = 1 — это два хвоста одной и той же статистики. Типичная подгонка — увидеть 0.054, «вспомнить», что α можно взять 0.1, или сравнить с α самое маленькое из трёх p. План для того и пишут заранее, чтобы таких соблазнов не было.

## task: choose | Какой тест | plus

Напишите функцию `choose_test(kind, groups, paired=False, skewed=False)`, которая по описанию задачи возвращает название теста:

- `kind="share"`, `groups=2` → `"proportions_ztest"`;
- `kind="category"` (любое число групп) → `"chi2_contingency"`;
- `kind="mean"`, `groups=1` → `"ttest_1samp"`;
- `kind="mean"`, `groups=2`, `paired=True` → `"ttest_rel"`;
- `kind="mean"`, `groups=2`, `skewed=True` → `"mannwhitneyu"`;
- `kind="mean"`, `groups=2` (иначе) → `"ttest_ind"`.

### starter
```python
def choose_test(kind, groups, paired=False, skewed=False):
    ...

choose_test("mean", 2)
```

### check
```python
f = need('choose_test')
cases = [(('share', 2), {}, 'proportions_ztest'), (('category', 3), {}, 'chi2_contingency'), (('category', 2), {}, 'chi2_contingency'),
         (('mean', 1), {}, 'ttest_1samp'), (('mean', 2), {'paired': True}, 'ttest_rel'), (('mean', 2), {'skewed': True}, 'mannwhitneyu'),
         (('mean', 2), {}, 'ttest_ind')]
for args, kw, want in cases:
    got = f(*args, **kw)
    assert got == want, f'choose_test{args}{", " + str(kw) if kw else ""} = {got!r}, а нужно {want!r}.'
```

### hint
Сначала разберите `kind`, внутри «mean» — число групп, потом `paired` и `skewed`.

### hint
Порядок проверок внутри «mean» важен: `groups == 1` → `paired` → `skewed` → иначе `ttest_ind`.

### solution
```python
def choose_test(kind, groups, paired=False, skewed=False):
    if kind == "share":
        return "proportions_ztest"
    if kind == "category":
        return "chi2_contingency"
    if groups == 1:
        return "ttest_1samp"
    if paired:
        return "ttest_rel"
    if skewed:
        return "mannwhitneyu"
    return "ttest_ind"

choose_test("mean", 2)
```

### explain
Функция повторяет логику аналитика: что сравниваем (доли, категории, средние), сколько групп, связаны ли наблюдения, похоже ли распределение на колокол. Проверку `paired` до `skewed` делают потому, что для парных скошенных данных есть свой тест (Уилкоксона), а не Манна — Уитни.

## task: agree | Формула и перемешивание согласны | plus

Сравните долю опозданий в KZN-2 и KZN-1 двумя способами: z-тестом для долей (`p_z`) и перестановочным тестом на 4 000 перемешиваний (`p_perm`, `rng = np.random.default_rng(2)`). Оба p-value должны быть близки. Сохраните ещё `diff_pp` — разницу долей в п.п. (1 знак).

### starter
```python
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
x = ok[ok["shop_id"].isin(["KZN-2", "KZN-1"])]
late = (x["actual_min"] > x["promised_min"]).to_numpy()
grp = (x["shop_id"] == "KZN-2").to_numpy()
rng = np.random.default_rng(2)

```

### check
```python
from statsmodels.stats.proportion import proportions_ztest as _z
import numpy as _np
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
x = ok[ok['shop_id'].isin(['KZN-2', 'KZN-1'])]
late = (x['actual_min'] > x['promised_min']).to_numpy()
g = (x['shop_id'] == 'KZN-2').to_numpy()
pz = _z([late[g].sum(), late[~g].sum()], [g.sum(), (~g).sum()])[1]
assert close(need('p_z'), pz, 6e-5), f'p_z = {need("p_z")}, а нужно около {pz:.6f}.'
assert abs(need('p_perm') - pz) < 0.004, f'p_perm = {need("p_perm")} — должно быть близко к p_z = {pz:.4f}.'
assert close(need('diff_pp'), round((late[g].mean() - late[~g].mean()) * 100, 1)), f'diff_pp = {need("diff_pp")}.'
```

### hint
z-тест: `proportions_ztest([late[grp].sum(), late[~grp].sum()], [grp.sum(), (~grp).sum()])`.

### hint
Перестановки — как в уроке «Проверка гипотез: логика и p-value».

### solution
```python
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
x = ok[ok["shop_id"].isin(["KZN-2", "KZN-1"])]
late = (x["actual_min"] > x["promised_min"]).to_numpy()
grp = (x["shop_id"] == "KZN-2").to_numpy()
rng = np.random.default_rng(2)
z, p_z = proportions_ztest([late[grp].sum(), late[~grp].sum()], [grp.sum(), (~grp).sum()])
observed = late[grp].mean() - late[~grp].mean()
diffs = np.array([late[s].mean() - late[~s].mean() for s in (rng.permutation(grp) for _ in range(4000))])
p_perm = (np.abs(diffs) >= abs(observed)).mean()
diff_pp = round(observed * 100, 1)
```

### explain
Формула и симуляция дают почти одно и то же p. Формулы — это сокращённый путь, который работает, когда выборки достаточно большие. Перемешивание — запасной вариант на любой случай.

## task: report | Фраза для отчёта | star

Напишите функцию `compare_shares(late_a, late_b)`: принимает два массива `True/False` (опоздания в группах A и B) и возвращает строку вида

`"A: 30.0 %, B: 20.0 %, разница 10.0 п.п. (95 % ДИ -1.9…21.9), p = 0.1025"`

— доли и разница с 1 знаком, интервал разницы — по формуле из урока «Доверительные интервалы», p — z-тест для долей, 4 знака. Между границами интервала — символ многоточия «…», а не три точки. Образец выше — для выдуманных групп 30 из 100 и 20 из 100. Проверьте функцию на KZN-2 (A) и KZN-1 (B): результат — в `phrase`.

### starter
```python
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

def compare_shares(late_a, late_b):
    ...

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = ok["actual_min"] > ok["promised_min"]
phrase = compare_shares(late[ok["shop_id"] == "KZN-2"].to_numpy(), late[ok["shop_id"] == "KZN-1"].to_numpy())
phrase
```

### check
```python
import numpy as _np
from statsmodels.stats.proportion import proportions_ztest as _z
def _w(a, b):
    p1, p2, n1, n2 = a.mean(), b.mean(), len(a), len(b)
    se = _np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    dd = p1 - p2
    p = _z([a.sum(), b.sum()], [n1, n2])[1]
    return f'A: {p1 * 100:.1f} %, B: {p2 * 100:.1f} %, разница {dd * 100:.1f} п.п. (95 % ДИ {(dd - 1.96 * se) * 100:.1f}…{(dd + 1.96 * se) * 100:.1f}), p = {p:.4f}'
f = need('compare_shares')
a = _np.array([True] * 30 + [False] * 70)
b = _np.array([True] * 20 + [False] * 80)
assert f(a, b) == _w(a, b), f'Для 30/100 и 20/100:\n{f(a, b)!r}\nа нужно\n{_w(a, b)!r}'
assert need('phrase').startswith('A: ') and ' п.п. (95 % ДИ ' in need('phrase'), 'phrase — результат функции на KZN-2 и KZN-1.'
```

### hint
Внутри: `p1, p2 = a.mean(), b.mean()`, `n1, n2 = len(a), len(b)`, SE разницы — `np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)`.

### hint
Формат в f-строке: `{p1 * 100:.1f}`, `{p:.4f}`. Многоточие — символ «…».

### solution
```python
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

def compare_shares(late_a, late_b):
    p1, p2 = late_a.mean(), late_b.mean()
    n1, n2 = len(late_a), len(late_b)
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p1 - p2
    z, p = proportions_ztest([late_a.sum(), late_b.sum()], [n1, n2])
    return (f"A: {p1 * 100:.1f} %, B: {p2 * 100:.1f} %, разница {diff * 100:.1f} п.п. "
            f"(95 % ДИ {(diff - 1.96 * se) * 100:.1f}…{(diff + 1.96 * se) * 100:.1f}), p = {p:.4f}")

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = ok["actual_min"] > ok["promised_min"]
phrase = compare_shares(late[ok["shop_id"] == "KZN-2"].to_numpy(), late[ok["shop_id"] == "KZN-1"].to_numpy())
phrase
```

### explain
Эта функция — заготовка для анализа A/B-теста в следующем уроке: там ровно такой вопрос — различаются ли доли в двух группах, насколько и насколько уверенно.
