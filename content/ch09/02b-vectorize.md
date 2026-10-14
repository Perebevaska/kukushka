---
title: "Без циклов: векторизация и замер времени"
lead: "`X @ w` считает прогноз для всей таблицы одной командой — а цикл по строкам делает то же в десятки раз дольше. Разбираемся, почему так, как честно замерить время `time.perf_counter()` и `%timeit` и как переписать условия `if` в цикле через `np.where`."
files: [deliveries.csv]
recap:
  - "Векторизация — операция над целым массивом (`X @ w`, `np.where`, арифметика столбцов) вместо цикла по строкам. На сотнях тысяч строк — в десятки раз быстрее; `apply(axis=1)` — скрытый цикл."
  - "Время замеряют `t0 = time.perf_counter()` … `time.perf_counter() - t0`, повторяют несколько раз и берут наименьшее; в Jupyter — `%timeit`. Сначала сверяют ответы (`np.allclose`), потом скорость; один замер шумит."
  - "`np.where(условие, если да, если нет)` заменяет `if` внутри цикла; вложенный `np.where` — цепочку `if … elif … else`."
  - "Если циклов два, векторизуют длинный: короткий цикл (по 6 кофейням) оставляют, а внутри считают сразу для всех строк, потом `argmin(axis=1)`."
---

## Цикл или одна операция

В уроке «Матрицы» прогноз линейной модели для всей таблицы мы получали одной операцией `X @ w`. Тот же прогноз можно посчитать и обычным циклом по строкам, как в главе 1. Ответ будет тот же, но на сотнях тысяч строк цикл работает заметно дольше, а `X @ w` почти мгновенно. Для «Зерна» это разница между отчётом, который пересчитывается при каждом открытии, и отчётом, которого ждут. Разберёмся, откуда разница и как её измерить.

::: tip Аналогия
Кассир пробивает сто одинаковых стаканов капучино. Можно пробить сто раз по одному: каждый раз найти позицию в меню, проверить цену, добавить строку. Можно ввести «капучино × 100» одной строкой. Цикл в Python — первый способ, операция над целым массивом — второй. Только компьютер не устаёт, он просто на каждой строке цикла заново выясняет, что за числа перед ним и что с ними делать.
:::

### Сначала на игрушке

Три доставки и веса из урока «Матрицы» (раздел «Матрица на вектор»). Цикл берёт строку, умножает её элементы на веса, складывает и прибавляет свободный член — это те же 33.8, 25.3 и 38.2, что мы считали там руками. `X @ w + b` делает те же три вычисления одной командой:

```python
import numpy as np
X = np.array([
    [1.0, 2, 1],
    [4.0, 1, 0],
    [6.0, 4, 0],
])
w = np.array([3.9, 1.7, 18.5])
b = 8.0

out = []
for row in X:                                    # строка за строкой
    out.append(row[0] * w[0] + row[1] * w[1] + row[2] * w[2] + b)
print("цикл:  ", np.round(out, 1))
print("вектор:", (X @ w + b).round(1))
```

### Замер времени

Теперь 100 тысяч строк. Время измерим секундомером `time.perf_counter()`: он возвращает текущее время в секундах с точностью до долей микросекунды. Разность двух показаний и есть длительность. Один замер шумит: первый вызов бывает медленнее следующих, а любой вызов может совпасть с работой другой программы. Поэтому замер повторяют несколько раз и берут **наименьшее** время — оно ближе всего к «чистой» скорости кода.

```python
import time
import numpy as np

rng = np.random.default_rng(0)
X = rng.uniform(0, 10, size=(100_000, 3))       # 100 тысяч доставок, 3 признака
w = np.array([3.9, 1.7, 18.5])
b = 8.0

def loop_predict(X, w, b):
    out = []
    for row in X:                                # Python обходит строки по одной
        out.append(row[0] * w[0] + row[1] * w[1] + row[2] * w[2] + b)
    return np.array(out)

def best_time(f, repeats=3):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()                 # засекли
        f()
        times.append(time.perf_counter() - t0)   # остановили: сколько секунд прошло
    return min(times)                            # наименьшее из повторов

t_loop = best_time(lambda: loop_predict(X, w, b))
t_vec = best_time(lambda: X @ w + b)
same = np.allclose(loop_predict(X, w, b), X @ w + b)

print(f"цикл:   {t_loop:.3f} с")
print(f"вектор: {t_vec:.4f} с")
print(f"быстрее в {t_loop / t_vec:.0f} раз; ответы совпадают: {same}")
```

**Что здесь происходит:**

- `rng.uniform(0, 10, size=(100_000, 3))` — таблица 100 000 × 3 из случайных чисел от 0 до 10. Сами числа неважны, важен размер.
- `t0 = time.perf_counter()` перед действием и `time.perf_counter() - t0` после — шаблон любого замера.
- `best_time(f, repeats=3)` вызывает функцию `f` три раза, замеряет каждый вызов и возвращает наименьшее время. `lambda: loop_predict(X, w, b)` — функция без аргументов (лямбды были в главе 1): `best_time` вызывает её, когда ей нужно, а не мы сразу.
- `loop_predict` — тот же расчёт, что в игрушке, только для каждой из 100 000 строк.
- `np.allclose(loop_predict(X, w, b), X @ w + b)` — ответы совпадают с точностью до округления. Сравнивать скорость имеет смысл, только если оба способа считают одно и то же.

**Почему так быстрее.** В цикле Python на каждой строке заново достаёт элементы, проверяет их типы и создаёт новые числа-объекты. Это сто тысяч раз одна и та же подготовительная работа. `X @ w` — одна команда: numpy один раз проверяет форму и тип, а затем считает готовым циклом на C по сплошному блоку памяти. Операцию над целым массивом вместо цикла по элементам называют **векторизацией**. Арифметика столбцов pandas (`df["a"] * df["b"]`) тоже векторизована, а `df.apply(..., axis=1)` — это скрытый цикл по строкам.

::: figure loop-vs-vector
Условная схема: в цикле подготовительная работа повторяется на каждой из 100 000 строк, а `X @ w` проверяет форму и тип один раз и дальше только считает. Время — из замера `%timeit` в этом уроке.
:::

**Как читать результат.** Точные секунды меняются от запуска к запуску и от компьютера к компьютеру. Важен порядок разницы: в браузере курса обычно выходит несколько десятков раз, в обычном Python — до сотни-двух. Если убрать `best_time` и замерить по одному разу, ускорение может показаться в несколько раз меньше: первый вызов `X @ w` медленнее следующих.

### В Jupyter: `%timeit`

В своём блокноте удобнее magic-команды из урока «Jupyter: руки на клавиатуре» главы 2. `%timeit` сам запускает выражение много раз и печатает среднее и разброс. В браузере курса и в обычном `.py`-файле magic-команд нет, там работает `time.perf_counter()`.

```python static
%timeit loop_predict(X, w, 8.0)
%timeit X @ w + 8.0
```

Вывод на одном из наших компьютеров:

```text
250 ms ± 29.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
901 μs ± 67.2 μs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)
```

Читаем: цикл — 250 миллисекунд, `X @ w` — 901 микросекунда, то есть 0.9 миллисекунды (μs — миллионная доля секунды). Разница — около 280 раз: в обычном Python на своём компьютере разрыв бывает больше, чем в браузере. `7 runs` — семь серий замеров. `1,000 loops each` — быструю операцию `%timeit` повторил по тысяче раз в каждой серии, чтобы время вообще можно было измерить.

::: quiz
Нужно посчитать скидку для 2 миллионов чеков: `amount × rate`. Какой вариант векторизован?

- [x] `df["amount"] * df["rate"]`
  > Операция над целыми столбцами: pandas передаёт её numpy, и тот считает одним циклом на C.
- [ ] `df.apply(lambda r: r["amount"] * r["rate"], axis=1)`
  > `apply` с `axis=1` вызывает функцию Python для каждой строки отдельно. Это тот же цикл, только спрятанный, и на 2 миллионах строк он медленный.
- [ ] `[a * r for a, r in zip(df["amount"], df["rate"])]`
  > Списковое включение короче цикла `for`, но это всё равно Python-цикл по двум миллионам пар.
- [ ] `for i in range(len(df)): df.loc[i, "disc"] = df.loc[i, "amount"] * df.loc[i, "rate"]`
  > Самый медленный вариант: цикл, да ещё с поиском по индексу на каждой строке.
:::

{{practice: best-of}}

## Условия без цикла: `np.where`

В цикле часто стоит `if`: «если доставка дальше 8 км — добавить 100 ₽». Векторная замена — `np.where(условие, значение_если_да, значение_если_нет)`. Условие — массив `True/False` той же длины, и для каждой строки берётся одно из двух значений. Сравним на четырёх доставках:

```python
import numpy as np
km = np.array([3.0, 9.5, 8.0, 12.0])
p = 60 + 14 * km                       # базовая оплата всех четырёх сразу

out = []
for k, pk in zip(km, p):               # цикл с if
    if k > 8:
        pk += 100
    out.append(pk)
print("цикл:    ", np.round(out, 1))
print("np.where:", np.where(km > 8, p + 100, p))
```

**Что здесь происходит:**

- `km > 8` — массив `[False, True, False, True]`: условие проверено сразу для всех четырёх. Ровно 8 км — не «больше 8», надбавки нет.
- `np.where(km > 8, p + 100, p)` — там, где `True`, берётся `p + 100`, где `False` — `p`. Получились те же 102, 293, 172 и 328, что и в цикле.
- Оба варианта ответа (`p + 100` и `p`) numpy считает целиком для всех строк, а потом выбирает. Поэтому в ветки нельзя класть то, что ломается на «чужих» строках, — например, деление на столбец с нулями.

Цепочку `if … elif … else` записывают вложенным `np.where`: `np.where(km > 8, 100, np.where(km > 3, 50, 0))` — «больше 8 — 100, иначе больше 3 — 50, иначе 0». Условия проверяются по порядку, как в цикле: первое сработавшее и решает.

{{practice: disc, tiers, apply-col}}

::: warn Типичные ошибки
- **Один замер.** Первый запуск бывает медленнее из-за подготовки, а любой запуск может попасть на работу другой программы. Повторяйте замер и берите наименьшее время, или пользуйтесь `%timeit`.
- **Сравнили скорость, не сверив ответы.** Быстрый вариант с ошибкой бесполезен. Сначала `np.allclose(a, b)`, потом секунды.
- **В замер попало лишнее.** Чтение файла или `print` внутри замеряемого кода. Секундомер ставят вплотную вокруг того, что сравнивают.
- **`apply(axis=1)` считают векторизацией.** Код короче цикла, но работает так же медленно. Ищите вариант через столбцы, `np.where` или `@`.
:::

**Если циклов два — векторизуйте длинный.** Бывает, что убрать все циклы трудно: например, для 30 000 заказов найти ближайшую из шести кофеен. Цикл по шести кофейням стоит копейки, медленно работает цикл по заказам. Поэтому оставляют короткий цикл, а внутри считают сразу для всех заказов: на каждом шаге — расстояние от всех заказов до одной кофейни (`np.abs(orders - shop).sum(axis=1)`). Шесть таких столбцов складывают в таблицу 30 000 × 6 функцией `np.column_stack([столбец1, столбец2, …])` — она ставит одномерные массивы рядом как столбцы. Номер ближайшей кофейни для каждого заказа даёт `argmin(axis=1)`, а сколько заказов досталось каждой кофейне, считает `np.bincount(номера, minlength=6)` — число вхождений каждого номера от 0 до 5.

{{practice: vectorize, nearest-shop}}

## Практика

## task: disc | Скидка на крупные чеки | warmup

Акция: на чеки дороже 500 ₽ скидка 10 %, остальные оплачиваются полностью. В заготовке — восемь чеков `amount`. Без цикла, через `np.where`, посчитайте `to_pay` — сколько заплатит каждый гость (массив той же длины), и `saved` — сколько гости сэкономили всего, округлите до 1 знака.

### starter
```python
import numpy as np

amount = np.array([320, 540, 500, 1250, 80, 760, 499, 501])

```

### check
```python
import numpy as _np
_a = _np.array([320, 540, 500, 1250, 80, 760, 499, 501])
_p = _np.where(_a > 500, _a * 0.9, _a)
got = _np.asarray(need('to_pay'), dtype=float)
assert got.shape == _p.shape, f'to_pay — массив из {len(_a)} сумм, по одной на чек, а у вас форма {got.shape}.'
assert not _np.allclose(got, _np.where(_a >= 500, _a * 0.9, _a)) or _np.allclose(got, _p), 'Чек ровно на 500 ₽ получил скидку, а скидка — только дороже 500: условие amount > 500.'
assert _np.allclose(got, _p), f'to_pay = {[float(x) for x in got]}, а нужно {[float(x) for x in _p]}.'
assert close(need('saved'), round(float(_a.sum() - _p.sum()), 1), 0.051), f'saved = {need("saved")}: сумма чеков минус сумма к оплате.'
assert 'for ' not in _code and 'while ' not in _code, 'Решите без цикла: условие проверяет np.where сразу для всех чеков.'
```

### hint
Условие для всех чеков сразу — `amount > 500`. В `np.where` три аргумента: условие, значение «если да», значение «если нет».

### hint
`to_pay = np.where(amount > 500, amount * 0.9, amount)`; экономия — `amount.sum() - to_pay.sum()`.

### solution
```python
import numpy as np

amount = np.array([320, 540, 500, 1250, 80, 760, 499, 501])
to_pay = np.where(amount > 500, amount * 0.9, amount)
saved = round(float(amount.sum() - to_pay.sum()), 1)
print(to_pay, saved)
```

### explain
Скидку получили четыре чека: 540, 1250, 760 и 501 ₽. Чек ровно на 500 ₽ и чек на 499 ₽ остались без скидки — граница «дороже 500» строгая, как и `>` в условии. Всего гости сэкономили 305.1 ₽. Тот же код без изменений сработает и для восьми миллионов чеков.

## task: best-of | Секундомер с повторами | warmup

Напишите функцию `best_time(f, repeats=5)`: она вызывает функцию `f` (без аргументов) `repeats` раз, замеряет каждый вызов через `time.perf_counter()` и возвращает наименьшее время в секундах (`float`). Затем замерьте ею сумму чисел до миллиона: `t_sum = best_time(lambda: sum(range(1_000_000)))`.

### starter
```python
import time

def best_time(f, repeats=5):
    ...

```

### check
```python
import time as _t
f = need('best_time')
_calls = []
def _work():
    _calls.append(1)
    if len(_calls) == 1:                       # первый вызов медленный, остальные — мгновенные
        s = 0
        for i in range(300_000):
            s += i
r = f(_work, 4)
assert len(_calls) == 4, f'best_time(f, 4) вызвала f {len(_calls)} раз, а нужно 4: по разу на каждый повтор.'
assert isinstance(r, float) and r > 0, f'best_time вернула {r!r}: нужно одно число — время в секундах.'
_t0 = _t.perf_counter(); s = 0
for i in range(300_000):
    s += i
_heavy = _t.perf_counter() - _t0
assert r < _heavy / 5, f'Вернулось {r:.4f} с — это похоже на время медленного первого вызова или на среднее. Нужно наименьшее из повторов: min(...).'
_calls.clear(); f(_work)
assert len(_calls) == 5, f'Без второго аргумента best_time вызвала f {len(_calls)} раз, а по умолчанию повторов 5.'
ts = need('t_sum')
assert isinstance(ts, float) and 0 < ts < 60, f't_sum = {ts!r}: время в секундах от best_time(lambda: sum(range(1_000_000))).'
```

### hint
Внутри — цикл `for _ in range(repeats):`, в нём шаблон замера: `t0 = time.perf_counter()`, вызов `f()`, разность `time.perf_counter() - t0` в список.

### hint
После цикла верните `min(times)`. Значение по умолчанию задаётся прямо в заголовке: `def best_time(f, repeats=5):`.

### solution
```python
import time

def best_time(f, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        f()
        times.append(time.perf_counter() - t0)
    return min(times)

t_sum = best_time(lambda: sum(range(1_000_000)))
print(f"{t_sum:.4f} с")
```

### explain
Проверка подсунула функцию, у которой первый вызов медленный, а остальные мгновенные, — так ведёт себя и настоящий код при «прогреве». Среднее из повторов утянуло бы этот выброс в ответ, а наименьшее — нет. Цикл `for` здесь уместен: он идёт по пяти повторам, а не по строкам данных. Это тот же приём, что делает `%timeit` в Jupyter, только `%timeit` ещё сам подбирает число повторов.

## task: tiers | Надбавка курьеру по дальности | base

Курьерам платят надбавку по дальности доставки: до 2 км включительно — 0 ₽, больше 2 и до 5 км включительно — 40 ₽, больше 5 км — 90 ₽. Для всех доставок из `deliveries.csv` (заготовка: массив `km`) посчитайте без цикла `bonus` — надбавку за каждую доставку. Сохраните `total_bonus` — сумму надбавок (`int`), `n_mid` — сколько доставок получили 40 ₽, и `n_far` — сколько получили 90 ₽.

### setup
```python
import numpy as np
import pandas as pd
km = pd.read_csv("deliveries.csv")["distance_km"].values
```

### starter
```python
import numpy as np

```

### check
```python
import numpy as _np
k0 = need('km')
_b = _np.where(k0 > 5, 90, _np.where(k0 > 2, 40, 0))
got = _np.asarray(need('bonus'), dtype=float)
assert got.shape == _b.shape, f'bonus — по числу на доставку ({len(k0)}), а у вас форма {got.shape}.'
_wrong = _np.where(k0 >= 5, 90, _np.where(k0 >= 2, 40, 0))
assert _np.allclose(got, _b) or not _np.allclose(got, _wrong), 'Ровно 2 и ровно 5 км попали в следующую ступень. «До 2 км включительно» — это km > 2 для надбавки 40.'
_flip = _np.where(k0 > 2, 40, _np.where(k0 > 5, 90, 0))
assert _np.allclose(got, _b) or not _np.allclose(got, _flip), 'Надбавки 90 ₽ нет ни у кого: первым проверяется условие km > 2, и оно «съедает» дальние доставки. Начните с самого строгого условия km > 5.'
assert _np.allclose(got, _b), f'bonus не совпадает у {int((~_np.isclose(got, _b)).sum())} доставок.'
assert need('total_bonus') == int(_b.sum()), f'total_bonus = {need("total_bonus")}.'
assert need('n_mid') == int((_b == 40).sum()), f'n_mid = {need("n_mid")}.'
assert need('n_far') == int((_b == 90).sum()), f'n_far = {need("n_far")}.'
assert 'for ' not in _code and 'while ' not in _code, 'Решите без цикла: вложенный np.where.'
```

### hint
Три ступени — это `if … elif … else`, а в numpy — вложенный `np.where`: снаружи самое строгое условие, внутри — следующее.

### hint
`bonus = np.where(km > 5, 90, np.where(km > 2, 40, 0))`. Количество — `(bonus == 40).sum()`.

### solution
```python
import numpy as np

bonus = np.where(km > 5, 90, np.where(km > 2, 40, 0))
total_bonus = int(bonus.sum())
n_mid = int((bonus == 40).sum())
n_far = int((bonus == 90).sum())
print(total_bonus, n_mid, n_far)
```

### explain
Из 1877 доставок 955 получили по 40 ₽, 225 — по 90 ₽, остальные 697 — без надбавки; всего 58 450 ₽, около 31 ₽ на доставку. Порядок условий решает так же, как в цепочке `if … elif`: если первым проверить `km > 2`, дальние доставки получат 40 ₽ и до проверки `km > 5` дело не дойдёт.

## task: apply-col | apply или столбцы | base

Сбор за упаковку: 15 ₽ за каждую позицию, но если позиций 4 и больше — фиксированно 60 ₽; заказы дороже 1500 ₽ упаковываются бесплатно. В заготовке — таблица доставок `d` (из `deliveries.csv`), функция `fee_apply` для `d.apply(fee_apply, axis=1)` и секундомер `best_time` из задачи «Секундомер с повторами». Напишите `fee_col(d)` — тот же расчёт через столбцы и `np.where`, без `apply` и циклов. Замерьте обе версии через `best_time`: `t_apply`, `t_col`; сохраните `speedup = t_apply / t_col` и `total` — сумму сборов по всем доставкам (`int`).

### setup
```python
import time
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")

def best_time(f, repeats=3):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        f()
        times.append(time.perf_counter() - t0)
    return min(times)
```

### starter
```python
import numpy as np

def fee_apply(r):
    if r["amount"] > 1500:
        return 0
    if r["items"] >= 4:
        return 60
    return 15 * r["items"]

def fee_col(d):
    ...

# готово, как в теории: d, best_time
```

### check
```python
import numpy as _np
d0 = need('d')
_f = _np.where(d0['amount'] > 1500, 0, _np.where(d0['items'] >= 4, 60, 15 * d0['items']))
got = _np.asarray(need('fee_col')(d0), dtype=float)
assert got.shape == _f.shape, f'fee_col вернула форму {got.shape}, а нужно {_f.shape}: по сбору на доставку.'
assert _np.allclose(got, _f), f'fee_col не совпадает с fee_apply у {int((~_np.isclose(got, _f)).sum())} доставок. Сравните на первых строках: d.head().apply(fee_apply, axis=1).'
_names = need('fee_col').__code__.co_names
assert not {'apply', 'iterrows', 'itertuples'} & set(_names), 'Внутри fee_col не должно быть apply и перебора строк — только столбцы и np.where.'
ta, tc = need('t_apply'), need('t_col')
assert ta > 0 and tc > 0, 't_apply и t_col — положительные времена в секундах от best_time.'
assert close(need('speedup'), ta / tc, max(0.02 * ta / tc, 0.6)), f'speedup = {need("speedup")}, а t_apply / t_col = {ta / tc:.1f}.'
assert ta / tc > 2, f'Версия через столбцы быстрее всего в {ta / tc:.1f} раза. Замеряете ли вы именно fee_col(d) и d.apply(fee_apply, axis=1)?'
assert need('total') == int(_f.sum()), f'total = {need("total")}.'
```

### hint
Условия те же, что в `fee_apply`, только для целых столбцов: `d["amount"] > 1500`, `d["items"] >= 4`. Цепочка `if … return` — это вложенный `np.where`, самое первое условие — снаружи.

### hint
`np.where(d["amount"] > 1500, 0, np.where(d["items"] >= 4, 60, 15 * d["items"]))`. Замер: `t_apply = best_time(lambda: d.apply(fee_apply, axis=1))`, `t_col = best_time(lambda: fee_col(d))`.

### solution
```python
import numpy as np

def fee_apply(r):
    if r["amount"] > 1500:
        return 0
    if r["items"] >= 4:
        return 60
    return 15 * r["items"]

def fee_col(d):
    return np.where(d["amount"] > 1500, 0,
                    np.where(d["items"] >= 4, 60, 15 * d["items"]))

t_apply = best_time(lambda: d.apply(fee_apply, axis=1))
t_col = best_time(lambda: fee_col(d))
speedup = t_apply / t_col
total = int(fee_col(d).sum())
print(f"apply {t_apply:.4f} с, столбцы {t_col:.5f} с, быстрее в {speedup:.0f} раз; сборов {total} ₽")
```

### explain
Сборов набирается 63 090 ₽: 37 заказов дороже 1500 ₽ упакованы бесплатно, у 391 — по 60 ₽. Таблица всего на 1877 строк, а разница уже в десятки раз: `apply(axis=1)` на каждой строке создаёт объект-строку и вызывает функцию Python, а `np.where` проходит столбцы один раз. Код через столбцы ещё и короче проверять: условия видны в одной строке.

## task: vectorize | Оплата курьеров без цикла | base

За каждую доставку курьер получает 60 ₽ плюс 14 ₽ за километр. За дальнюю доставку (больше 8 км) добавляется 100 ₽, а в дождь вся сумма умножается на 1.3. В заготовке — 100 000 доставок (`km`, `rain`) и функция `pay_loop`, которая считает оплату циклом. Напишите функцию `pay_vec(km, rain)`, которая считает то же без цикла. Замерьте обе функции через `time.perf_counter()`: время в секундах — `t_loop` и `t_vec`. Сохраните `same` — совпадают ли ответы (`np.allclose`), `speedup` — во сколько раз векторный вариант быстрее (`t_loop / t_vec`), и `total` — общую сумму выплат, округлённую до рубля (`int`).

### starter
```python
import time
import numpy as np

rng = np.random.default_rng(1)
n = 100_000
km = rng.uniform(0.5, 12, n).round(1)
rain = rng.random(n) < 0.2                 # True — шёл дождь

def pay_loop(km, rain):
    out = np.empty(len(km))
    for i in range(len(km)):
        p = 60 + 14 * km[i]
        if km[i] > 8:
            p += 100
        if rain[i]:
            p *= 1.3
        out[i] = p
    return out

def pay_vec(km, rain):
    ...

```

### check
```python
import numpy as _np
_r = _np.random.default_rng(1); _km = _r.uniform(0.5, 12, 100_000).round(1); _rain = _r.random(100_000) < 0.2
_p = 60 + 14 * _km + _np.where(_km > 8, 100, 0); _p = _np.where(_rain, _p * 1.3, _p)
f = need('pay_vec')
got = _np.asarray(f(_km, _rain), dtype=float)
assert got.shape == _p.shape, f'pay_vec вернула массив формы {got.shape}, а нужно {_p.shape}: по одной сумме на доставку.'
assert _np.allclose(got[_km > 8], _p[_km > 8]) or not _np.allclose(got[_km <= 8], _p[_km <= 8]), 'Для доставок дальше 8 км сумма не сходится: не забыли надбавку 100 ₽ до умножения на 1.3?'
assert _np.allclose(got, _p), 'pay_vec считает не так, как pay_loop. Сравните на первых строках: pay_loop(km[:5], rain[:5]) и pay_vec(km[:5], rain[:5]).'
assert need('same') is True or need('same') == True, 'same должно быть True: сравните ответы двух функций через np.allclose.'
tl, tv = need('t_loop'), need('t_vec')
assert tl > 0 and tv > 0, 't_loop и t_vec — положительные длительности в секундах: perf_counter() после минус perf_counter() до.'
assert tl < 600 and tv < 600, 'Время похоже не на секунды. Это разность двух показаний time.perf_counter().'
assert close(need('speedup'), tl / tv, max(0.02 * tl / tv, 0.6)), f'speedup = {need("speedup")}, а t_loop / t_vec = {tl / tv:.1f}.'
assert tl / tv > 2, f'Векторный вариант быстрее всего в {tl / tv:.1f} раза. Похоже, внутри pay_vec остался цикл по доставкам.'
assert need('total') == int(round(_p.sum())), f'total = {need("total")}. Сумма всех выплат pay_vec(km, rain), округлённая до рубля.'
```

### hint
Работайте с массивами целиком: `60 + 14 * km` сразу даёт базовую оплату всех доставок. Условия «если» превращаются в `np.where`.

### hint
`np.where(km > 8, 100, 0)` — надбавка 100 там, где доставка дальняя, иначе 0. Дождь: `np.where(rain, p * 1.3, p)`.

### hint
Замер: `t0 = time.perf_counter()`, затем `a = pay_loop(km, rain)`, затем `t_loop = time.perf_counter() - t0`. То же для `pay_vec`.

### solution
```python
import time
import numpy as np

rng = np.random.default_rng(1)
n = 100_000
km = rng.uniform(0.5, 12, n).round(1)
rain = rng.random(n) < 0.2                 # True — шёл дождь

def pay_loop(km, rain):
    out = np.empty(len(km))
    for i in range(len(km)):
        p = 60 + 14 * km[i]
        if km[i] > 8:
            p += 100
        if rain[i]:
            p *= 1.3
        out[i] = p
    return out

def pay_vec(km, rain):
    p = 60 + 14 * km + np.where(km > 8, 100, 0)
    return np.where(rain, p * 1.3, p)

t0 = time.perf_counter()
a = pay_loop(km, rain)
t_loop = time.perf_counter() - t0

t0 = time.perf_counter()
b = pay_vec(km, rain)
t_vec = time.perf_counter() - t0

same = bool(np.allclose(a, b))
speedup = t_loop / t_vec
total = int(round(b.sum()))
print(f"цикл {t_loop:.3f} с, вектор {t_vec:.4f} с, быстрее в {speedup:.0f} раз; всего {total} ₽")
```

### explain
Каждая ветка `if` превратилась в `np.where`: условие проверяется сразу для всего массива, и для каждой строки выбирается одно из двух значений. Порядок важен так же, как в цикле: сначала надбавка 100 ₽, потом умножение на 1.3. Если поменять их местами, у дальних доставок в дождь надбавка не умножится, и сумма разойдётся с `pay_loop`. Ускорение в браузере — обычно в десятки раз; если у вас вышло всего в несколько раз, запустите ещё раз: первый вызов функции numpy медленнее следующих. Выплат набирается около 19.3 млн ₽. Секунды у вас будут свои, а итоговая сумма — ровно та же: от скорости ответ не зависит.

## task: nearest-shop | Ближайшая кофейня для 30 тысяч заказов | plus

Каждый заказ доставки отдаём ближайшей кофейне по манхэттенскому расстоянию (урок «Векторы»). В заготовке 30 000 заказов (`orders`, координаты в км), 6 кофеен (`shops`) и функция `nearest_loop` с двумя вложенными циклами. Напишите `nearest_vec(orders, shops)` без цикла по заказам. Цикл по шести кофейням оставить можно: короткий цикл не страшен, медленно работает длинный. Функция возвращает номер ближайшей кофейни для каждого заказа. Замерьте обе функции (`t_loop`, `t_vec`, секунды) и сохраните `speedup`. Ещё сохраните `load` — сколько заказов досталось каждой кофейне (массив из 6 чисел), и `busiest` — номер самой загруженной кофейни.

### starter
```python
import time
import numpy as np

rng = np.random.default_rng(2)
orders = rng.uniform(0, 20, size=(30_000, 2))
shops = np.array([[3, 4], [15, 5], [10, 12], [4, 16], [17, 17], [9, 2]], dtype=float)

def nearest_loop(orders, shops):
    res = np.empty(len(orders), dtype=int)
    for i in range(len(orders)):
        best, best_d = -1, np.inf
        for j in range(len(shops)):
            d = abs(orders[i, 0] - shops[j, 0]) + abs(orders[i, 1] - shops[j, 1])
            if d < best_d:
                best, best_d = j, d
        res[i] = best
    return res

def nearest_vec(orders, shops):
    ...

```

### check
```python
import numpy as _np
_o = _np.random.default_rng(2).uniform(0, 20, size=(30_000, 2))
_s = _np.array([[3, 4], [15, 5], [10, 12], [4, 16], [17, 17], [9, 2]], dtype=float)
_D = _np.column_stack([_np.abs(_o - s).sum(axis=1) for s in _s]); _w = _D.argmin(axis=1)
got = _np.asarray(need('nearest_vec')(_o, _s))
assert got.shape == _w.shape, f'nearest_vec вернула форму {got.shape}, а нужно {_w.shape}: по номеру кофейни на заказ.'
_De = _np.column_stack([_np.linalg.norm(_o - s, axis=1) for s in _s])
assert (got == _w).all() or not (got == _De.argmin(axis=1)).all(), 'Номера совпадают с ближайшими по прямой. Нужно манхэттенское расстояние: сумма модулей разностей.'
assert (got == _w).all(), f'Не совпало у {int((got != _w).sum())} заказов из 30 000. Сравните с nearest_loop на первых 10 заказах.'
tl, tv = need('t_loop'), need('t_vec')
assert tl > 0 and tv > 0, 't_loop и t_vec — положительные длительности в секундах.'
assert close(need('speedup'), tl / tv, max(0.02 * tl / tv, 0.6)), f'speedup = {need("speedup")}, а t_loop / t_vec = {tl / tv:.1f}.'
assert tl / tv > 2, f'Ускорение всего {tl / tv:.1f} раза. Похоже, в nearest_vec остался цикл по заказам.'
ld = _np.bincount(_w, minlength=6)
assert _np.array_equal(_np.asarray(need('load')), ld), f'load = {need("load")}, а нужно {ld.tolist()}: число заказов у каждой из 6 кофеен.'
assert need('busiest') == int(ld.argmax()), f'busiest = {need("busiest")}.'
```

### hint
Посчитайте сразу таблицу расстояний: строка — заказ, столбец — кофейня (30 000 × 6). Тогда ближайшая кофейня — номер минимума в каждой строке.

### hint
Расстояния от всех заказов до одной кофейни `s` — `np.abs(orders - s).sum(axis=1)`. Шесть таких столбцов склеиваются через `np.column_stack([... for s in shops])`.

### hint
`D.argmin(axis=1)` — номер минимума в каждой строке. Подсчёт заказов: `np.bincount(nearest, minlength=6)`, самая загруженная — `load.argmax()`.

### solution
```python
import time
import numpy as np

rng = np.random.default_rng(2)
orders = rng.uniform(0, 20, size=(30_000, 2))
shops = np.array([[3, 4], [15, 5], [10, 12], [4, 16], [17, 17], [9, 2]], dtype=float)

def nearest_loop(orders, shops):
    res = np.empty(len(orders), dtype=int)
    for i in range(len(orders)):
        best, best_d = -1, np.inf
        for j in range(len(shops)):
            d = abs(orders[i, 0] - shops[j, 0]) + abs(orders[i, 1] - shops[j, 1])
            if d < best_d:
                best, best_d = j, d
        res[i] = best
    return res

def nearest_vec(orders, shops):
    D = np.column_stack([np.abs(orders - s).sum(axis=1) for s in shops])   # 30 000 × 6
    return D.argmin(axis=1)

t0 = time.perf_counter()
a = nearest_loop(orders, shops)
t_loop = time.perf_counter() - t0

t0 = time.perf_counter()
b = nearest_vec(orders, shops)
t_vec = time.perf_counter() - t0

speedup = t_loop / t_vec
load = np.bincount(b, minlength=6)
busiest = int(load.argmax())
print(f"совпадает: {(a == b).all()}, быстрее в {speedup:.0f} раз")
print("заказов по кофейням:", load, "| самая загруженная:", busiest)
```

### explain
Приём «цикл по короткой оси, вектор по длинной»: шесть итераций по кофейням, в каждой — одна операция над всеми 30 000 заказами. Python-цикл делает 6 шагов вместо 180 000, отсюда ускорение в десятки раз. Больше всего заказов у кофейни 1 (5949), меньше всего — у кофейни 5 (3148): она стоит у края карты, и «её» территория меньше. `argmin` при равных расстояниях берёт первый номер, как и `<` в цикле, поэтому ответы совпадают полностью. Если бы вместо модулей вы взяли расстояние по прямой, часть заказов у границ территорий ушла бы другой кофейне.
