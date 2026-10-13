---
title: Precision, recall и F1
lead: "Матрица ошибок — четыре числа, а сравнивать модели удобнее по одному-двум. Учимся задавать матрице два вопроса бизнеса — «бонусы ушли по адресу?» и «скольких уходящих нашли?», — сводить ответы в F1 и решать, какая ошибка дороже."
files: [guests_churn.csv]
recap:
  - "Точность (precision) = TP / (TP + FP): какая доля бонусов досталась тем, кто действительно уходил. Не путать с accuracy — долей всех правильных ответов."
  - "Полнота (recall) = TP / (TP + FN): какую долю уходящих модель нашла. Полнота = 1 − доля пропущенных из урока «Матрица ошибок»."
  - "`precision_score`, `recall_score`, `f1_score` из `sklearn.metrics` принимают (факт, прогноз); если модель никого не назвала положительным, точность не определена — `zero_division=0` делает её нулём без предупреждения."
  - "F1 = 2·P·R / (P + R) — гармоническое среднее: оно близко к меньшей из двух метрик, поэтому «бонус всем» не получает высокий балл за полноту 1."
  - "`classification_report(y_true, y_pred)` печатает точность, полноту и F1 для каждого класса, `support` — сколько объектов класса в данных; `output_dict=True` возвращает то же словарём."
  - "Дорог FP (лишнее действие) — следим за точностью; дорог FN (пропуск) — за полнотой. Обычно одну метрику держат не ниже планки, а другую делают как можно больше."
  - "F-beta (`fbeta_score`) — F1 с перекосом: β > 1 важнее полнота, β < 1 — точность."
---

## Бонусы по адресу: точность

В прошлом уроке мы разложили ответы леса из 100 деревьев (пример теории) на четыре клетки: TN = 443, FP = 23, FN = 44, TP = 90. Четыре числа — это подробно, но неудобно: модели хочется сравнивать по одной-двум метрикам. Отдел лояльности задаёт матрице два вопроса. Первый: **из тех, кому мы отправили бонус, какая доля действительно собиралась уйти?**

Бонус получили все, кого модель назвала уходящими, — это столбец «модель: уйдёт», TP + FP. По адресу из них TP. Отношение называют **точностью** (precision):

$$
\text{precision} = \frac{TP}{TP + FP}
$$

У леса это 90 / (90 + 23) ≈ 0.80: четыре бонуса из пяти потрачены не зря, пятый ушёл гостю, который и так бы остался.

В `sklearn.metrics` есть готовая функция. Аргументы — как у `confusion_matrix`: сначала факт, потом прогноз.

```python
from sklearn.metrics import precision_score

fact = [1, 0, 1, 1, 0, 0, 0, 0]
pred = [1, 1, 0, 1, 0, 0, 1, 0]
print(precision_score(fact, pred))
print(2 / (2 + 2))
```

Модель назвала уходящими четверых, правы были в двух случаях — точность 0.5.

::: warn Точность — это не accuracy
По-русски слово «точность» часто говорят и про accuracy. В курсе мы разделяем: **accuracy — доля правильных ответов** среди всех, **точность (precision)** — доля правильных среди ответов «уйдёт». Accuracy смотрит на всю матрицу, точность — только на её правый столбец. Если в отчёте написано «точность модели 89 %», уточните, о чём речь.
:::

{{practice: by-hand, perfect-prec}}

## Скольких нашли: полнота

Второй вопрос отдела лояльности: **из всех, кто ушёл, скольких модель заметила?** Ушедшие — это нижняя строка матрицы, FN + TP. Найдены из них TP. Отношение называют **полнотой** (recall):

$$
\text{recall} = \frac{TP}{TP + FN}
$$

У леса 90 / (90 + 44) ≈ 0.67. Это та же «доля пропущенных уходящих» из прошлого урока, только с другой стороны: полнота = 1 − FN / (FN + TP). Пропустили треть — нашли две трети.

```python
from sklearn.metrics import recall_score

fact = [1, 0, 1, 1, 0, 0, 0, 0]
pred = [1, 1, 0, 1, 0, 0, 1, 0]
print(recall_score(fact, pred))
print(2 / (2 + 1))
```

Чтобы не путать формулы, держите в голове матрицу: точность считается **по столбцу** «модель: уйдёт», полнота — **по строке** «факт: ушёл». В обеих наверху TP, а внизу к нему добавляется своя ошибка: у точности — FP (ложная тревога), у полноты — FN (пропуск).

::: figure pr-cm
Матрица леса. Точность — по столбцу «прогноз: уйдёт» (синяя рамка): сколько бонусов ушло по адресу. Полнота — по строке «факт: ушёл» (красная рамка): скольких уходящих нашли. TP — на пересечении.
:::

::: tip Аналогия
Бариста выкрикивает не имя, а «капучино!», и чашки разбирают из зала. Точность — какая доля отданных чашек попала к тем, кто капучино действительно заказывал; полнота — какая доля заказавших свою чашку получила. Если сварить капучино на весь зал, полнота станет 1, а точность упадёт; если отдавать чашку, только когда уверен в госте, точность высокая, но часть заказавших останется без кофе.
:::

::: predict
```python static
from sklearn.metrics import precision_score, recall_score
fact = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
pred = [1, 1, 0, 0, 1, 0, 0, 0, 0, 0]
print(round(precision_score(fact, pred), 2), recall_score(fact, pred))
```

- `0.5 0.67`
- [x] `0.67 0.5`
- `0.7 0.5`

Почему: модель назвала уходящими троих (TP = 2, FP = 1) — точность 2/3. Ушедших четверо, найдены двое (FN = 2) — полнота 2/4. Вариант 0.7 — это accuracy: 7 правильных ответов из 10.
:::

{{practice: all-bonus}}

## Правило, дерево и лес

Посчитаем обе метрики для трёх подходов из прошлого урока: правила «не был больше 45 дней», дерева глубины 2 и леса.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

preds = {
    "правило 45 дней": (X_test["days_since_last"] > 45).astype(int),
    "дерево глубины 2": DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train).predict(X_test),
    "лес": RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict(X_test),
}
for name, pred in preds.items():
    print(f"{name:17} precision {precision_score(y_test, pred):.2f}  recall {recall_score(y_test, pred):.2f}")
```

**Что здесь происходит:**

- Тот же словарь `preds`, что в уроке «Матрица ошибок», — меняются только метрики в цикле.
- `precision_score(y_test, pred)` и `recall_score(y_test, pred)` — по умолчанию для класса 1 («уйдёт»).
- `:.2f` в f-строке — два знака после запятой, чтобы столбцы читались ровно.

Картина та же, что в матрицах, но теперь в двух числах:

- **правило** очень точное (около 0.85), но находит только 41 % уходящих;
- **дерево глубины 2** — наоборот: находит около 78 % уходящих, но каждый третий бонус уходит не по адресу;
- **лес** посередине: точность около 0.80, полнота около 0.67.

Это обычная ситуация: точность и полноту трудно поднять одновременно. Модель, которая смелее называет гостей уходящими, находит больше (полнота растёт), но и ошибается тревогами чаще (точность падает).

::: note Модель никого не назвала уходящим
У базовой модели «никто не уйдёт» TP + FP = 0, и точность — это 0 / 0. sklearn вернёт 0 и выведет предупреждение `UndefinedMetricWarning`. Если такой случай ожидаем, добавьте `zero_division=0`: результат тот же, но без предупреждения. Полнота у неё честно равна 0 — ни одного найденного.
:::

```python
from sklearn.metrics import precision_score, recall_score

fact = [1, 0, 1, 0, 0]
pred = [0, 0, 0, 0, 0]
print(precision_score(fact, pred, zero_division=0), recall_score(fact, pred))
```

{{practice: forest-prf, three-models}}

## F1: одно число для двух

Двумя числами сравнивать неудобно: у правила лучше точность, у дерева — полнота. Хочется одну метрику, которая растёт, только когда хороши обе. Первая мысль — взять среднее. Но проверим её на крайнем случае: **бонус всем гостям**. Полнота 1 (нашли всех уходящих), точность 0.22 (по адресу только доля ушедших). Обычное среднее — 0.61, почти как у приличной модели. А модель бесполезна: она просто раздаёт бонусы всем.

Поэтому используют **гармоническое среднее** — его называют **F1-мерой** (F1 score):

$$
F_1 = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision} + \text{recall}}
$$

Гармоническое среднее всегда тянется к меньшему из двух чисел. Если одна метрика близка к нулю, F1 тоже маленькая, как бы ни была велика вторая. У «бонуса всем» F1 ≈ 0.37.

::: figure f1-mean
Точность и полнота четырёх подходов из урока, их обычное среднее и F1. Чем дальше друг от друга две метрики, тем сильнее F1 отстаёт от обычного среднего: у «бонуса всем» полнота 1, но F1 всего 0.37.
:::

::: predict
```python static
p, r = 1.0, 0.1
print(round((p + r) / 2, 2), round(2 * p * r / (p + r), 2))
```

- `0.55 0.55`
- [x] `0.55 0.18`
- `0.18 0.55`

Почему: обычное среднее делит сумму пополам — 0.55, хотя модель находит лишь каждого десятого. Гармоническое: 2 · 1.0 · 0.1 / 1.1 ≈ 0.18 — ближе к слабой стороне.
:::

В sklearn — `f1_score(y_true, y_pred)`. Если подставить в формулу TP, FP и FN, получится $F_1 = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$: метрика вообще не смотрит на TN — на верно не тронутых лояльных гостей. Поэтому при дисбалансе её нельзя «набрать» на частом классе, как accuracy.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

preds = {
    "бонус всем": [1] * len(y_test),
    "правило 45 дней": (X_test["days_since_last"] > 45).astype(int),
    "дерево глубины 2": DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train).predict(X_test),
    "лес": RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict(X_test),
}
for name, pred in preds.items():
    print(f"{name:17} F1 {f1_score(y_test, pred):.2f}")
```

По F1 порядок такой: лес (около 0.73) чуть впереди дерева (около 0.71), правило (около 0.55) заметно отстаёт, «бонус всем» — последний. По accuracy правило и дерево почти вровень (около 85 и 86 %); F1 показывает, что правило слишком многих пропускает.

::: deep F-beta: когда одна ошибка важнее
F1 считает точность и полноту равноправными. Если полнота важнее, берут **F-beta** — `fbeta_score(y_true, y_pred, beta=2)`: при β = 2 полнота весит больше, при β = 0.5 — точность. F1 — это F-beta при β = 1.
:::

{{practice: p-f1, f-beta}}

## classification_report

Чтобы не вызывать три функции, в sklearn есть сводка — `classification_report(y_true, y_pred)`. Она печатает точность, полноту и F1 сразу **для каждого класса**.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pred = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict(X_test)

print(classification_report(y_test, pred))
```

Как читать:

- строка **1** — наши метрики для уходящих: precision 0.80, recall 0.67, F1 0.73;
- строка **0** — те же метрики, если считать «положительным» класс оставшихся. Полнота 0.95 — это доля оставшихся, которых модель верно не тронула, то есть 1 − доля лишних бонусов из урока «Матрица ошибок»;
- **support** — сколько гостей каждого класса в тесте: 466 и 134;
- **accuracy** — доля правильных ответов, 0.89;
- **macro avg** — простое среднее по двум классам, **weighted avg** — среднее с весами по support. Взвешенное среднее тянется к частому классу и при дисбалансе выглядит лучше, чем модель работает на редком.

Для акции удержания главное — строка 1. Функции `precision_score`, `recall_score`, `f1_score` по умолчанию считают именно её: класс 1 — положительный.

Отчёт можно получить не текстом, а словарём — `output_dict=True`. Ключи — названия классов строками (`"0"`, `"1"`) и строк сводки:

```python
from sklearn.metrics import classification_report

fact = [1, 0, 1, 1, 0, 0, 0, 0]
pred = [1, 1, 0, 1, 0, 0, 1, 0]
report = classification_report(fact, pred, output_dict=True)
print(list(report))
print(round(report["1"]["recall"], 3), report["1"]["support"])
```

::: quiz
В `classification_report` для леса строка weighted avg заметно лучше строки 1. Отдел лояльности спрашивает, как модель находит уходящих. Какие цифры им показать?

- [x] Строку 1: точность, полноту и F1 для класса уходящих
  > Вопрос именно про уходящих, а их метрики — в строке класса 1. Средние смешивают их с метриками оставшихся.
- [ ] Weighted avg: она учитывает размер классов, значит, честнее
  > Веса — это support, а оставшихся гостей в тесте больше чем втрое (466 против 134). Поэтому взвешенное среднее тянется к классу 0 и приукрашивает работу на редком классе.
- [ ] Macro avg: она не зависит от дисбаланса
  > Macro avg честнее взвешенной, но всё равно смешивает два класса: хорошая полнота на оставшихся маскирует пропуски уходящих.
- [ ] Accuracy из той же сводки
  > Accuracy считает правильные ответы по всем гостям и при дисбалансе набирается на оставшихся — про поиск уходящих она почти ничего не говорит.
:::

{{practice: report, newcomers}}

## Что важнее: точность или полнота

Какая метрика главная, решает не sklearn, а цена ошибок — та, что мы считали в конце урока «Матрица ошибок».

- **Дорог пропуск (FN)** — следим за **полнотой**. Бонус на кофе стоит 300 ₽, а ушедший гость уносит тысячи: лучше раздать лишние бонусы, чем упустить уходящих. Так же устроены поиск мошеннических платежей и проверка на брак: пропущенный случай обходится дороже лишней проверки.
- **Дорога ложная тревога (FP)** — следим за **точностью**. Если «удержание» — это звонок управляющего кофейней или сертификат на 1500 ₽, каждая ошибка заметна, а ресурс ограничен. Так же со спам-фильтром: важное письмо в спаме хуже, чем пропущенная рассылка.

На практике договариваются так: одну метрику держат не ниже планки, а другую делают как можно больше. Например, «найти не меньше 70 % уходящих, и при этом как можно точнее» или «не меньше 80 % бонусов по адресу, и найти как можно больше». F1 удобна, когда цены ошибок сопоставимы или неизвестны и нужна одна общая оценка.

::: quiz
Бонус стоит дорого, бюджет маленький. На какую метрику смотреть прежде всего?

- [x] Точность: важно, чтобы бонусы получили действительно уходящие, а не все подряд
  > Каждая ложная тревога — потраченный впустую бонус, поэтому при дорогом бонусе важно, чтобы тревоги оправдывались.
- [ ] Полнота: найти всех уходящих любой ценой
  > При маленьком бюджете высокая полнота обычно означает много бонусов не по адресу. Полнота важнее в обратной ситуации — когда бонус дешёвый, а уход дорог.
- [ ] Accuracy
  > При 22 % уходящих даже модель «никто не уйдёт» набирает 78 % — accuracy плохо различает полезные и бесполезные модели.
- [ ] Неважно, F1 решает всё
  > F1 одинаково ценит обе ошибки, а здесь цена у них разная.
:::

## Разберём вместе: выбор по планке

Отдел лояльности ставит условие: **найти не меньше 70 % уходящих**, а среди подходящих взять самый точный. Распишем матрицы трёх подходов (тест, 134 ушедших, 466 оставшихся):

| подход | TP | FP | FN | полнота TP / (TP + FN) | точность TP / (TP + FP) |
|---|---|---|---|---|---|
| правило 45 дней | 55 | 10 | 79 | 55 / 134 = **0.41** | 55 / 65 = 0.85 |
| дерево глубины 2 | 104 | 55 | 30 | 104 / 134 = **0.78** | 104 / 159 = 0.65 |
| лес | 90 | 23 | 44 | 90 / 134 = **0.67** | 90 / 113 = 0.80 |

1. Планка по полноте: правило (0.41) и лес (0.67) не проходят, проходит только дерево (0.78).
2. Среди прошедших выбирать не из чего — берём дерево, хотя его точность самая низкая.

Что получилось: лучший по F1 (лес, 0.73) проиграл, потому что задача сформулирована иначе. А если бы планка была «точность не ниже 0.75, полнота — максимальная», победил бы лес (0.80 и 0.67), а дерево не прошло бы. Метрику выбирают до сравнения моделей, из цены ошибок, — иначе всегда найдётся метрика, в которой выиграла понравившаяся модель.

::: figure recall-plan
Три подхода на плоскости «полнота — точность». Сначала отсекаем всё, что левее планки 0.70, потом среди оставшихся берём самый точный. Проходит только дерево глубины 2.
:::

И одна оговорка: лесу не обязательно проигрывать. С порогом ниже 0.5 он может пройти планку по полноте, сохранив точность выше, чем у дерева. Это тема следующего урока.

::: warn Типичные ошибки
- **Знаменатели перепутаны.** Точность — делим на всех, кого модель назвала уходящими (столбец); полнота — на всех реально ушедших (строка).
- **Порядок аргументов.** `precision_score(pred, fact)` вернёт полноту, и наоборот: функции не знают, где факт.
- **Weighted avg вместо строки 1.** Взвешенное среднее при дисбалансе приукрашивает модель — для редкого класса смотрите его строку.
- **Метрику выбирают после результатов.** Сначала цена ошибок и планка, потом сравнение.
:::

::: tip Одна модель — много пар точность/полнота
Пока мы меняли баланс, только перебирая модели. Но у одной и той же модели можно двигать точность и полноту, не переобучая её, — через порог вероятности. Это следующий урок.
:::

{{practice: recall-plan}}

## Практика

## task: by-hand | Метрики по формулам | warmup

У леса из прошлого урока на тесте TP = 90, FP = 23, FN = 44. Посчитайте по формулам, без sklearn (все — 3 знака):

- `prec` — точность;
- `rec` — полноту;
- `f1` — F1 по точности и полноте (из неокруглённых значений).

### starter
```python
tp, fp, fn = 90, 23, 44

```

### check
```python
_p, _r = 90 / 113, 90 / 134
_f = 2 * _p * _r / (_p + _r)
_got_p, _got_r = need('prec'), need('rec')
if close(_got_p, round(_r, 3)) and close(_got_r, round(_p, 3)):
    raise AssertionError('Точность и полнота перепутаны местами. Точность — делим на всех, кому дали бонус (TP + FP); полнота — на всех ушедших (TP + FN).')
assert close(_got_p, round(_p, 3)), f'prec = {_got_p}, а нужно {round(_p, 3)}. Точность — это TP / (TP + FP).'
assert close(_got_r, round(_r, 3)), f'rec = {_got_r}, а нужно {round(_r, 3)}. Полнота — это TP / (TP + FN).'
assert not close(need('f1'), round((_p + _r) / 2, 3)), f'f1 = {need("f1")} — это обычное среднее. F1 — гармоническое: 2 · P · R / (P + R).'
assert close(need('f1'), round(_f, 3)), f'f1 = {need("f1")}, а нужно {round(_f, 3)}. Формула: 2 · P · R / (P + R).'
```

### hint
Точность: `tp / (tp + fp)`, полнота: `tp / (tp + fn)`. Округлять — в самом конце.

### hint
Сохраните неокруглённые значения в `p` и `r`, тогда `f1 = round(2 * p * r / (p + r), 3)`.

### solution
```python
tp, fp, fn = 90, 23, 44
p = tp / (tp + fp)
r = tp / (tp + fn)
prec = round(p, 3)
rec = round(r, 3)
f1 = round(2 * p * r / (p + r), 3)
```

### explain
Точность 0.796, полнота 0.672, F1 0.729 — она ближе к меньшей из двух. Обычное среднее дало бы 0.734: разница небольшая, потому что точность и полнота здесь недалеко друг от друга. Чем сильнее они расходятся, тем сильнее F1 «штрафует» за слабую сторону.

## task: p-f1 | F1 своими руками | warmup

Соберите программу: посчитать точность и полноту функциями sklearn, по ним — F1 по формуле и вывести её рядом с `f1_score`. Должны получиться два одинаковых числа.

### parsons
```python
from sklearn.metrics import precision_score, recall_score, f1_score
fact = [1, 0, 1, 1, 0, 1, 0, 0]
pred = [1, 1, 1, 0, 0, 0, 0, 0]
p = precision_score(fact, pred)
r = recall_score(fact, pred)
f1 = 2 * p * r / (p + r)
print(round(f1, 3), round(f1_score(fact, pred), 3))
```

### check
```python
assert close(need('f1'), 4 / 7), f'f1 = {need("f1")}. Проверьте формулу 2 · p · r / (p + r) и что p и r посчитаны до неё.'
assert _lines == ['0.571 0.571'], f'Программа вывела {_lines}, а ожидалась одна строка с двумя одинаковыми числами 0.571.'
```

### hint
Функции нужно импортировать до использования, списки — создать до расчёта метрик, а `p` и `r` — до формулы F1.

## task: perfect-prec | Точность 100 % | warmup

Модель отметила для акции одного гостя из двенадцати — и угадала. Посчитайте функциями sklearn `prec`, `rec` и `f1` (3 знака).

### starter
```python
fact = [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0]
pred = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]

```

### check
```python
assert close(need('prec'), 1.0), f'prec = {need("prec")}. Модель назвала уходящим одного гостя, и он действительно ушёл — какая доля бонусов по адресу?'
assert close(need('rec'), 0.333), f'rec = {need("rec")}, а нужно 0.333. Ушедших в списке трое — скольких нашла модель?'
assert close(need('f1'), 0.5), f'f1 = {need("f1")}, а нужно 0.5. Используйте f1_score(fact, pred).'
```

### hint
`from sklearn.metrics import precision_score, recall_score, f1_score`; аргументы — сначала факт, потом прогноз.

### hint
Сначала посчитайте на пальцах: уходящих в `fact` трое, модель отметила одного, и он действительно уходит. Значит TP = 1, FP = 0, FN = 2. Точность — доля верных среди отмеченных, полнота — доля найденных среди всех уходящих. Сверьте с тем, что выдаст sklearn: здесь хорошо видно, что идеальная точность ещё не значит хорошую модель.

### solution
```python
from sklearn.metrics import precision_score, recall_score, f1_score

fact = [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0]
pred = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
prec = round(precision_score(fact, pred), 3)
rec = round(recall_score(fact, pred), 3)
f1 = round(f1_score(fact, pred), 3)
```

### explain
Идеальная точность легко достаётся осторожной модели: назвать уходящим одного самого очевидного гостя — и не ошибиться. Но двоих из трёх уходящих она пропустила. Поэтому точность без полноты (и наоборот) ничего не говорит о модели.

## task: forest-prf | Метрики леса | base

Обучите `RandomForestClassifier(n_estimators=50, random_state=0)` и сохраните для теста:

- `prec`, `rec`, `f1` — точность, полноту и F1 (3 знака);
- `bonuses` — сколько гостей теста получат бонус по прогнозу модели (целое).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_score as _ps, recall_score as _rs, f1_score as _fs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b)
_w = {'prec': round(_ps(_e, _p), 3), 'rec': round(_rs(_e, _p), 3), 'f1': round(_fs(_e, _p), 3)}
if close(need('prec'), round(_ps(_p, _e), 3)) and not close(need('prec'), _w['prec']):
    raise AssertionError('prec похоже посчитана с перепутанными аргументами. Сначала факт (y_test), потом прогноз.')
for _k, _v in _w.items():
    assert close(need(_k), _v), f'{_k} = {need(_k)}, а нужно {_v}. Проверьте модель (n_estimators=50, random_state=0) и что метрика считается на тесте.'
assert int(need('bonuses')) == int(_p.sum()), f'bonuses = {need("bonuses")}, а ожидалось {int(_p.sum())}. Бонус получает каждый, кого модель назвала уходящим: TP + FP.'
```

### hint
`pred = forest.predict(X_test)`, затем `precision_score(y_test, pred)` и т. д.

### hint
Число бонусов — сколько единиц в прогнозе: `pred.sum()`; не забудьте `int(...)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pred = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train).predict(X_test)
prec = round(precision_score(y_test, pred), 3)
rec = round(recall_score(y_test, pred), 3)
f1 = round(f1_score(y_test, pred), 3)
bonuses = int(pred.sum())
```

### explain
Лес из 50 деревьев отправит бонусы примерно 120 гостям из 600; около 79 % из них по адресу, и найдено около 69 % уходящих. Результат почти такой же, как у леса из 100 деревьев в теории.

## task: three-models | Таблица трёх подходов | base

Сравните на тесте правило `days_since_last > 45`, `DecisionTreeClassifier(max_depth=2, random_state=0)` и `RandomForestClassifier(n_estimators=50, random_state=0)`. Сохраните таблицу `scores`: индекс — `"правило"`, `"дерево"`, `"лес"`, столбцы `precision`, `recall`, `f1` (3 знака) и `cost` — потери в рублях по схеме урока «Матрица ошибок»: бонус 300 ₽ платим всем, кому отправили (TP и FP), пропущенный уходящий (FN) стоит 2 000 ₽. В `best_f1` — название строки с наибольшей F1, в `best_cost` — с наименьшими потерями.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_score as _ps, recall_score as _rs, f1_score as _fs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_preds = {
    'правило': (_b['days_since_last'] > 45).astype(int),
    'дерево': _T(max_depth=2, random_state=0).fit(_a, _c).predict(_b),
    'лес': _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b),
}
_w = {_k: {'precision': round(_ps(_e, _p), 3), 'recall': round(_rs(_e, _p), 3), 'f1': round(_fs(_e, _p), 3)} for _k, _p in _preds.items()}
_t = need('scores', _pd.DataFrame)
assert set(_t.index) == set(_w), f'В индексе scores: {list(_t.index)}, а нужны {list(_w)}. Возможно, таблицу нужно развернуть: .T'
assert {'precision', 'recall', 'f1'} <= set(_t.columns), f'Столбцы scores: {list(_t.columns)}, а нужны precision, recall и f1.'
for _k, _row in _w.items():
    for _m, _v in _row.items():
        assert close(_t.loc[_k, _m], _v), f'{_k}, {_m}: {_t.loc[_k, _m]}, а ожидалось {_v}. Проверьте прогноз этого подхода и порядок аргументов: сначала y_test.'
_bf = max(_w, key=lambda _k: _w[_k]['f1'])
assert need('best_f1') == _bf, f'best_f1 = {need("best_f1")!r}. Найдите строку с наибольшим f1: scores["f1"].idxmax().'
from sklearn.metrics import confusion_matrix as _cm
_cost = {}
for _k, _p in _preds.items():
    _tn, _fp, _fn, _tp = _cm(_e, _p).ravel()
    _cost[_k] = int(300 * (_tp + _fp) + 2000 * _fn)
assert 'cost' in _t.columns, 'Нужен столбец cost — потери в рублях.'
for _k, _v in _cost.items():
    assert close(_t.loc[_k, 'cost'], _v, 0.6), f'{_k}, cost: {_t.loc[_k, "cost"]}, а ожидалось {_v}. Бонус 300 ₽ — за TP и FP, 2000 ₽ — за каждый FN.'
assert need('best_cost') == min(_cost, key=_cost.get), f'best_cost = {need("best_cost")!r}. Строка с наименьшими потерями: scores["cost"].idxmin().'
```

### hint
Соберите словарь прогнозов, как в теории, и в цикле — словарь строк: `rows[name] = {"precision": ..., "recall": ..., "f1": ...}`.

### hint
`pd.DataFrame(rows).T.round(3)` превращает словарь словарей в таблицу (без `.T` названия подходов окажутся в столбцах). Лучшая строка — `scores["f1"].idxmax()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

preds = {
    "правило": (X_test["days_since_last"] > 45).astype(int),
    "дерево": DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train).predict(X_test),
    "лес": RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train).predict(X_test),
}
rows = {}
for name, pred in preds.items():
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    rows[name] = {"precision": precision_score(y_test, pred),
                  "recall": recall_score(y_test, pred),
                  "f1": f1_score(y_test, pred),
                  "cost": 300 * (tp + fp) + 2000 * fn}
scores = pd.DataFrame(rows).T.round(3)
best_f1 = scores["f1"].idxmax()
best_cost = scores["cost"].idxmin()
scores
```

### explain
У каждого подхода своя сильная сторона: у правила — точность, у дерева — полнота, у леса — баланс, и по F1 он впереди (0.733). Но по деньгам выигрывает дерево: 107 700 ₽ потерь против 119 100 ₽ у леса и 177 500 ₽ у правила. Пропуск стоит 2 000 ₽, бонус — 300 ₽, поэтому дереву, которое находит 104 уходящих против 92 у леса, лишние 30 бонусов обходятся дешевле. Лучшая F1 — не то же самое, что лучшие деньги.

## task: all-bonus | Бонус всем | base

Проверьте на тесте «модель», которая отправляет бонус **всем** гостям: прогноз — единица для каждого гостя `y_test`. Сохраните (3 знака):

- `prec_all`, `rec_all` — её точность и полноту;
- `mean_all` — обычное среднее точности и полноты;
- `f1_all` — её F1.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _e.mean()
assert close(need('rec_all'), 1.0), f'rec_all = {need("rec_all")}. Если бонус получают все, скольких ушедших мы нашли?'
assert close(need('prec_all'), round(_p, 3)), f'prec_all = {need("prec_all")}, а нужно {round(_p, 3)}. По адресу ушли бонусы только ушедшим — какая это доля всех гостей теста?'
assert close(need('mean_all'), round((_p + 1) / 2, 3)), f'mean_all = {need("mean_all")}, а нужно {round((_p + 1) / 2, 3)} — (точность + полнота) / 2 по неокруглённым значениям.'
assert close(need('f1_all'), round(2 * _p / (_p + 1), 3)), f'f1_all = {need("f1_all")}, а нужно {round(2 * _p / (_p + 1), 3)}. Посчитайте f1_score по тому же прогнозу.'
```

### hint
Прогноз «всем»: `pred = [1] * len(y_test)`.

### hint
Обычное среднее: `(precision_score(y_test, pred) + recall_score(y_test, pred)) / 2`, округлить в конце.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

pred = [1] * len(y_test)
p = precision_score(y_test, pred)
r = recall_score(y_test, pred)
prec_all = round(p, 3)
rec_all = round(r, 3)
mean_all = round((p + r) / 2, 3)
f1_all = round(f1_score(y_test, pred), 3)
```

### explain
Точность «бонуса всем» — это просто доля ушедших, 0.223. Обычное среднее дало бы 0.61 — почти как у правила «45 дней». F1 = 0.365 честно показывает, что такая «модель» ничего не умеет: гармоническое среднее не даёт спрятать плохую точность за идеальной полнотой.

## task: report | Отчёт по классам | base

Для `RandomForestClassifier(n_estimators=50, random_state=0)` получите `classification_report` словарём (`output_dict=True`) и сохраните из него:

- `rec1` — полноту для класса 1 (3 знака);
- `rec0` — полноту для класса 0 (3 знака);
- `support1` — сколько ушедших в тесте (целое);
- `macro_f1` — F1 из строки `macro avg` (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import classification_report as _cr
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_r = _cr(_e, _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b), output_dict=True)
assert close(need('rec1'), round(_r['1']['recall'], 3)), f'rec1 = {need("rec1")}, а нужно {round(_r["1"]["recall"], 3)}. Это report["1"]["recall"].'
assert close(need('rec0'), round(_r['0']['recall'], 3)), f'rec0 = {need("rec0")}, а нужно {round(_r["0"]["recall"], 3)}. Ключи классов в отчёте — строки: "0" и "1".'
assert int(need('support1')) == int(_r['1']['support']), f'support1 = {need("support1")}, а нужно {int(_r["1"]["support"])} — support из строки класса 1.'
assert close(need('macro_f1'), round(_r['macro avg']['f1-score'], 3)), f'macro_f1 = {need("macro_f1")}, а нужно {round(_r["macro avg"]["f1-score"], 3)}. Ключ строки — "macro avg", ключ метрики — "f1-score" (через дефис).'
```

### hint
`report = classification_report(y_test, pred, output_dict=True)`; посмотрите на ключи: `print(report["1"])`.

### hint
Названия метрик в словаре: `"precision"`, `"recall"`, `"f1-score"`, `"support"`. Строка сводки — `report["macro avg"]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pred = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train).predict(X_test)

report = classification_report(y_test, pred, output_dict=True)
rec1 = round(report["1"]["recall"], 3)
rec0 = round(report["0"]["recall"], 3)
support1 = int(report["1"]["support"])
macro_f1 = round(report["macro avg"]["f1-score"], 3)
```

### explain
Полнота для оставшихся — около 0.95, для уходящих — около 0.69: модель гораздо увереннее узнаёт частый класс. Macro F1 (около 0.83) — среднее двух F1 и выглядит лучше, чем работа модели на уходящих (около 0.73). Для акции удержания смотрите на строку класса 1.

## task: recall-plan | План по полноте | plus

Отдел лояльности ставит условие: модель должна находить **не меньше 70 %** уходящих гостей, а среди таких моделей нужна самая точная. Переберите деревья `DecisionTreeClassifier(max_depth=d, random_state=0)` для `d` от 1 до 8 и сохраните:

- `trees` — DataFrame со столбцами `depth`, `precision`, `recall`, `f1` (по строке на дерево, метрики на тесте, 3 знака);
- `best_depth` — глубину дерева, которое выполняет условие по полноте и среди таких имеет наибольшую точность (целое).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.metrics import precision_score as _ps, recall_score as _rs, f1_score as _fs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_rows = []
for _d in range(1, 9):
    _p = _T(max_depth=_d, random_state=0).fit(_a, _c).predict(_b)
    _rows.append({'depth': _d, 'precision': round(_ps(_e, _p), 3), 'recall': round(_rs(_e, _p), 3), 'f1': round(_fs(_e, _p), 3)})
_w = _pd.DataFrame(_rows)
_t = need('trees', _pd.DataFrame)
assert {'depth', 'precision', 'recall', 'f1'} <= set(_t.columns), f'Столбцы trees: {list(_t.columns)}, а нужны depth, precision, recall, f1.'
assert len(_t) == 8, f'В trees {len(_t)} строк, а глубин от 1 до 8 — восемь.'
_t = _t.sort_values('depth').reset_index(drop=True)
assert list(_t['depth']) == list(range(1, 9)), f'Глубины в trees: {list(_t["depth"])}, а нужны 1…8.'
for _i, _row in _w.iterrows():
    for _m in ('precision', 'recall', 'f1'):
        assert close(_t.loc[_i, _m], _row[_m]), f'Глубина {int(_row["depth"])}, {_m}: {_t.loc[_i, _m]}, а ожидалось {_row[_m]}. Проверьте random_state=0 и порядок аргументов метрик.'
_ok = _w[_w['recall'] >= 0.7]
_bd = int(_ok.loc[_ok['precision'].idxmax(), 'depth'])
_got = int(need('best_depth'))
if _got == int(_w.loc[_w['precision'].idxmax(), 'depth']) and _got != _bd:
    raise AssertionError(f'best_depth = {_got} — самое точное дерево, но оно находит меньше 70 % уходящих. Сначала оставьте строки с recall ≥ 0.7.')
assert _got == _bd, f'best_depth = {_got}, а ожидалось другое. Оставьте деревья с recall ≥ 0.7 и среди них возьмите наибольшую precision.'
```

### hint
Цикл `for d in range(1, 9):` — внутри обучите дерево, посчитайте три метрики и добавьте словарь в список `rows`. Затем `trees = pd.DataFrame(rows)`.

### hint
`ok = trees[trees["recall"] >= 0.7]`, затем строка с наибольшей точностью: `ok.loc[ok["precision"].idxmax(), "depth"]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import precision_score, recall_score, f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

rows = []
for d in range(1, 9):
    pred = DecisionTreeClassifier(max_depth=d, random_state=0).fit(X_train, y_train).predict(X_test)
    rows.append({"depth": d,
                 "precision": round(precision_score(y_test, pred), 3),
                 "recall": round(recall_score(y_test, pred), 3),
                 "f1": round(f1_score(y_test, pred), 3)})
trees = pd.DataFrame(rows)
ok = trees[trees["recall"] >= 0.7]
best_depth = int(ok.loc[ok["precision"].idxmax(), "depth"])
trees
```

### explain
Самое точное дерево — глубины 3 (около 0.94), но оно находит меньше половины уходящих и условие не выполняет. Полноту не ниже 0.7 дают только три дерева — глубины 2, 5 и 6, — и самое точное из них — глубины 6 (0.746 против 0.728 у глубины 5). Так выглядит выбор «одна метрика не ниже планки, другая — как можно больше». Честнее было бы выбирать глубину на кросс-валидации, а не на тесте (глава 6, урок «Честное сравнение моделей») — здесь мы упростили, чтобы сосредоточиться на метриках.

## task: newcomers | Кого лес ловит хуже | plus

В уроке «Матрица ошибок» оказалось, что среди пропущенных уходящих много новичков. Проверьте это метриками. Для `RandomForestClassifier(n_estimators=50, random_state=0)` посчитайте точность и полноту отдельно для новичков теста (`tenure_months <= 3`) и для остальных гостей теста (3 знака): `prec_new`, `rec_new`, `prec_old`, `rec_old`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_score as _ps, recall_score as _rs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _pd.Series(_RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b), index=_b.index)
_m = _b['tenure_months'] <= 3
_w = {'prec_new': round(_ps(_e[_m], _p[_m]), 3), 'rec_new': round(_rs(_e[_m], _p[_m]), 3),
      'prec_old': round(_ps(_e[~_m], _p[~_m]), 3), 'rec_old': round(_rs(_e[~_m], _p[~_m]), 3)}
for _k, _v in _w.items():
    _grp = 'новичков (tenure_months <= 3)' if _k.endswith('new') else 'остальных (tenure_months > 3)'
    assert close(need(_k), _v), f'{_k} = {need(_k)}, а нужно {_v}. Это метрика для {_grp}: и факт, и прогноз берутся по одной и той же маске.'
```

### hint
Сделайте прогноз Series с индексом теста: `pred = pd.Series(forest.predict(X_test), index=X_test.index)`. Тогда одна маска подходит и к `y_test`, и к `pred`.

### hint
`new = X_test["tenure_months"] <= 3`; метрики новичков — `recall_score(y_test[new], pred[new])`, остальных — с маской `~new`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
pred = pd.Series(forest.predict(X_test), index=X_test.index)

new = X_test["tenure_months"] <= 3
prec_new = round(precision_score(y_test[new], pred[new]), 3)
rec_new = round(recall_score(y_test[new], pred[new]), 3)
prec_old = round(precision_score(y_test[~new], pred[~new]), 3)
rec_old = round(recall_score(y_test[~new], pred[~new]), 3)
```

### explain
Точность в обеих группах почти одинаковая (около 0.8), а полнота у новичков около 0.5 против 0.7 у остальных: каждого второго уходящего новичка лес не замечает. У новичков мало истории — визитов и стажа, — и модели не на что опереться. Новичков в тесте всего 38, поэтому цифры шаткие, но направление совпадает с разбором ошибок из урока «Матрица ошибок». Средняя метрика по всем гостям прячет такие провалы — полезно считать её по сегментам.

## task: f-beta | Три меры — три победителя | star

В теории мы упомянули F-beta: `fbeta_score(y_true, y_pred, beta=...)` из `sklearn.metrics`. При `beta=2` полнота весит больше точности, при `beta=0.5` — наоборот, при `beta=1` это F1.

Для деревьев `DecisionTreeClassifier(max_depth=d, random_state=0)`, `d` от 1 до 8, посчитайте на тесте F1, F2 (`beta=2`) и F0.5 (`beta=0.5`). Сохраните целые числа:

- `d_f1` — глубину с наибольшей F1;
- `d_f2` — глубину с наибольшей F2;
- `d_f05` — глубину с наибольшей F0.5.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.metrics import fbeta_score as _fb
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = {1: {}, 2: {}, 0.5: {}}
for _d in range(1, 9):
    _p = _T(max_depth=_d, random_state=0).fit(_a, _c).predict(_b)
    for _beta in _s:
        _s[_beta][_d] = _fb(_e, _p, beta=_beta)
_w = {'d_f1': max(_s[1], key=_s[1].get), 'd_f2': max(_s[2], key=_s[2].get), 'd_f05': max(_s[0.5], key=_s[0.5].get)}
_tips = {'d_f1': 'beta=1 (или f1_score)', 'd_f2': 'beta=2 — полнота важнее', 'd_f05': 'beta=0.5 — точность важнее'}
if int(need('d_f2')) == _w['d_f05'] and int(need('d_f05')) == _w['d_f2'] and _w['d_f2'] != _w['d_f05']:
    raise AssertionError('d_f2 и d_f05 перепутаны: F2 — это beta=2, F0.5 — beta=0.5.')
for _k, _v in _w.items():
    assert int(need(_k)) == _v, f'{_k} = {need(_k)}, а ожидалось другое. Здесь нужна мера с {_tips[_k]}; переберите глубины 1…8 и возьмите глубину с наибольшим значением.'
```

### hint
Соберите таблицу, как в задаче «План по полноте»: для каждой глубины — словарь `{"depth": d, "f1": ..., "f2": ..., "f05": ...}`, где `f2 = fbeta_score(y_test, pred, beta=2)`.

### hint
Лучшая глубина по столбцу: `int(trees.loc[trees["f2"].idxmax(), "depth"])`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import fbeta_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

rows = []
for d in range(1, 9):
    pred = DecisionTreeClassifier(max_depth=d, random_state=0).fit(X_train, y_train).predict(X_test)
    rows.append({"depth": d,
                 "f1": fbeta_score(y_test, pred, beta=1),
                 "f2": fbeta_score(y_test, pred, beta=2),
                 "f05": fbeta_score(y_test, pred, beta=0.5)})
trees = pd.DataFrame(rows)
d_f1 = int(trees.loc[trees["f1"].idxmax(), "depth"])
d_f2 = int(trees.loc[trees["f2"].idxmax(), "depth"])
d_f05 = int(trees.loc[trees["f05"].idxmax(), "depth"])
print(trees.round(3))
print(d_f1, d_f2, d_f05)
```

### explain
Три меры выбрали три разных дерева. F2, которой важнее полнота, выбирает смелое дерево глубины 2 — то самое, что оказалось самым дешёвым в задаче о цене ошибок из урока «Матрица ошибок». F0.5, которой важнее точность, выбирает осторожное дерево глубины 3 с точностью около 0.94. F1 выбирает компромисс из середины — у глубин 5 и 6 она почти одинаковая. Метрика — это решение о ценах ошибок, записанное формулой: выбирайте её до того, как сравнивать модели.
