---
title: "Текст как данные: очистка и токены"
files: [reviews_text.csv]
lead: "Модели работают с числами, а отзывы гостей — это слова. Первый шаг любой работы с текстом — привести его к единому виду и разбить на слова-токены. Разбираемся с регистром, знаками препинания, частотами и стоп-словами — и с ловушкой: выкинуть «не» значит перевернуть смысл. В конце собираем первый мешок слов. Формы слов — в уроке «Леммы и словарь исключений»."
recap:
  - "Токенизация — разбиение текста на слова (токены). Простой способ — регулярное выражение `re.findall(r'[а-яё]+', text.lower())`."
  - "Приведение к нижнему регистру и удаление знаков препинания делают «Кофе», «кофе» и «кофе!» одним словом."
  - "`Counter` из модуля collections считает частоты слов; самые частые слова — служебные."
  - "Стоп-слова (предлоги, союзы) часто удаляют, но частицу «не» и подобные трогать нельзя: «не советую» ≠ «советую»."
  - "Мешок слов: текст → счётчик слов; порядок слов теряется, но для многих задач этого хватает."
---

## Отзывы гостей

`reviews_text.csv` — 2 400 отзывов из приложения: текст, оценка от 1 до 5 и основная тема (кофе, еда, обслуживание, доставка, цена, атмосфера), которую разметили сотрудники. Отзывы синтетические — собраны из типичных фраз, — но устроены как настоящие: короткие, с опечатками, иногда смешанные («кофе отличный, но…»).

```python
import pandas as pd
r = pd.read_csv("reviews_text.csv")
print(r.shape)
for t in r["text"].head(5):
    print("—", t)
print(r["rating"].value_counts().sort_index().to_dict())
```

**Что здесь происходит:**

- `r.shape` — 2400 строк и 5 столбцов: `review_id`, `shop_id`, `text`, `rating`, `topic`.
- `for t in r["text"].head(5)` — печатаем первые пять текстов целиком, по одному в строке: таблица pandas обрезала бы длинные строки.
- `value_counts().sort_index()` — сколько отзывов с каждой оценкой, по порядку оценок.

**Что видно:** отзывы короткие, в одну-две фразы; есть «вступления» («Хожу сюда давно.») и «концовки» («Всем советую.»); оценки 5 встречаются чаще всего, но плохих (1–3) тоже много — почти половина.

Задачи главы: понять по тексту, недоволен ли гость (тональность), и о чём он пишет (тема). Сначала текст нужно превратить во что-то, с чем работают модели.

## Токены

**Токенизация** — разбиение текста на единицы, обычно слова. Самый простой надёжный способ для русского текста — регулярное выражение «последовательность русских букв» после перевода в нижний регистр:

```python
import re
text = "Хожу сюда давно. Капучино с идеальной пенкой, но бариста грубил! Не советую."
tokens = re.findall(r"[а-яё]+", text.lower())
print(tokens)
```

- `text.lower()` — «Капучино» и «капучино» становятся одним словом;
- `[а-яё]+` — одна или больше русских букв подряд; всё остальное (точки, запятые, пробелы, цифры) служит разделителем. Буква «ё» в русском алфавите юникода стоит отдельно, поэтому её добавляют явно.

Весь путь, который проходит отзыв в этой главе, — на одной схеме. Токены, стоп-слова и мешок слов разберём в этом уроке, леммы — в уроке «Леммы и словарь исключений».

::: figure text-pipeline
Путь отзыва от строки до мешка слов: нижний регистр и токены, стоп-слова (отрицания «не» и «но» оставляем), леммы из таблицы `review_lemmas.csv`, счётчик слов. Жёлтым — леммы, которые лемматизатор угадал и которые стоит проверить.
:::

Посмотрим, что шаблон делает с неудобной строкой:

```python
import re
for text in ["Не-а, 2 капучино!!! Ёлки, 10/10", "кофе—супер", "Кофе,кофе и ещё раз КОФЕ"]:
    print(f"{text!r:36} → {re.findall(r'[а-яё]+', text.lower())}")
```

**Что здесь происходит:**

- «Не-а» распалось на два токена: дефис — не буква, значит разделитель.
- Цифры «2» и «10/10» исчезли: в шаблоне только буквы. Для отзывов это нормально, но для заказов («2 капучино») число было бы важным.
- «кофе—супер» разделилось по тире, хотя пробела нет: разделитель — любой не-буквенный символ.
- «КОФЕ», «Кофе» и «кофе» после `lower()` стали одним словом.
- `f"{text!r:36}"` — оформление вывода: `!r` печатает строку в кавычках, как `repr(text)`, а `:36` задаёт ширину поля, чтобы стрелки встали столбиком.

::: sql
Токенизация похожа на `STRING_SPLIT` или `regexp_split_to_table` в SQL: строка превращается в набор значений. Разница в том, что разделитель задаётся не одним символом, а правилом «всё, что не буква».
:::

Регулярные выражения мы использовали в главе 3 для очистки строк. Для английского текста шаблон был бы `[a-z]+`, для смешанного — `\w+` (любые буквы и цифры).

{{practice: tokenize, clean}}

## Частоты слов

Посчитаем, какие слова встречаются чаще всего. Удобный инструмент — `Counter` из стандартного модуля `collections`: он считает, сколько раз встретился каждый элемент списка.

```python
import re
from collections import Counter
import pandas as pd

r = pd.read_csv("reviews_text.csv")
words = Counter()
for text in r["text"]:
    words.update(re.findall(r"[а-яё]+", text.lower()))
print("разных слов:", len(words))
print(words.most_common(10))
```

**Что здесь происходит:**

- `Counter()` — пустой счётчик: словарь «слово → сколько раз».
- `words.update(список)` добавляет к счётчику каждое слово списка. Если слово уже было, его счёт растёт. Это то же самое, что `GROUP BY word` с `COUNT(*)` по всем отзывам сразу.
- `len(words)` — число **разных** слов (размер словаря); `most_common(10)` — десять самых частых.

Во всех отзывах — меньше 500 разных слов (в настоящих отзывах было бы много тысяч). Самые частые — «не», «кофе», предлоги и союзы. Такие частые служебные слова называют **стоп-словами**.

::: predict
```python static
from collections import Counter
c = Counter(["кофе", "вкусный", "кофе", "горький", "кофе"])
print(c.most_common(1))
```

- `[('вкусный', 1)]`
- [x] `[('кофе', 3)]`
- `{'кофе': 3}`

Почему: `most_common(n)` возвращает список из n пар «слово, частота» по убыванию частоты.
:::

{{practice: vocab, neg-words, bigrams}}

## Стоп-слова — осторожно

Стоп-слова часто удаляют: они есть почти в каждом тексте и сами по себе мало что говорят о его смысле. Но список стоп-слов нужно проверять под задачу. В стандартные списки для русского языка обычно входит «не» — а для тональности это одно из самых важных слов:

```python
import re
stop = {"и", "в", "с", "у", "но", "не", "на", "для", "а", "я"}
for text in ["Всем советую.", "Не советую.", "Приду ещё.", "Больше не приду."]:
    tokens = [w for w in re.findall(r"[а-яё]+", text.lower()) if w not in stop]
    print(f"{text:<18} → {tokens}")
```

**Что здесь происходит:**

- `stop` — множество (`set`): проверка `w not in stop` для множества мгновенная, даже если слов тысячи.
- Списковое выражение с условием оставляет только слова, которых нет в стоп-списке.
- `f"{text:<18}"` — выравнивание текста по левому краю в поле шириной 18 символов, чтобы стрелки стояли столбиком.

После удаления «не» отзыв «Не советую» превратился в «советую». Правило: из списка стоп-слов для анализа тональности убирают отрицания («не», «нет», «ни») и слова-переключатели вроде «но».

::: warn
Готовые списки стоп-слов (например, в nltk) составлены для поиска по документам, а не для тональности. Используйте их как отправную точку и обязательно проверяйте на своих данных — как мы только что сделали.
:::

::: quiz
Почему опасно выбрасывать «не» как стоп-слово в отзывах?

- [x] «не понравилось» превратится в «понравилось» — модель потеряет отрицание и спутает тональность
  > Списки стоп-слов составлены для поиска и тем, а для тональности частица «не» — один из главных сигналов.
- [ ] «не» — редкое слово
  > Наоборот, оно одно из самых частых.
- [ ] Стоп-слова нельзя удалять в принципе
  > Иногда это полезно, но смотреть нужно на задачу.
- [ ] Модель не обучится без всех слов
  > Обучится, но без «не» — хуже на отрицательных отзывах.
:::

{{practice: p-stop, rule}}

## Мешок слов

Самое простое числовое представление текста — **мешок слов** (bag of words): сколько раз встретилось каждое слово. Порядок слов при этом теряется: «кофе вкусный, но дорого» и «дорого, но кофе вкусный» — одинаковые мешки. Для классификации отзывов этого обычно достаточно. Ниже мы соберём таблицу мешков руками, а в уроке «Мешок слов и TF-IDF» её построит за нас `CountVectorizer`, и мы поправим веса слов (TF-IDF).

Соберём мешки для трёх коротких отзывов руками. Сначала **словарь** — все разные слова, по алфавиту: вкусный, горький, кофе, но, холодный. Потом для каждого отзыва — сколько раз встречается каждое слово словаря:

| отзыв | вкусный | горький | кофе | но | холодный |
|---|---|---|---|---|---|
| «Кофе вкусный, но холодный» | 1 | 0 | 1 | 1 | 1 |
| «Кофе горький, кофе холодный» | 0 | 1 | 2 | 0 | 1 |
| «Холодный, но вкусный кофе» | 1 | 0 | 1 | 1 | 1 |

Первая и третья строки совпали, хотя порядок слов разный.

::: figure bag-order
Отзывы 1 и 3 из таблицы: слова «высыпаются в мешок», порядок теряется, и в строке таблицы остаются только счётчики по словарю — у двух разных фраз они одинаковые.
:::

::: tip Аналогия
Мешок слов — как чек из кофейни, где позиции отсортированы по алфавиту: видно, что взяли два капучино и круассан, но не видно, в каком порядке их заказывали и что сказали бариста между ними. Для «о чём отзыв» этого обычно хватает, для «не вкусно, но быстро» против «вкусно, но не быстро» — нет.
:::

Теперь то же кодом:

```python
import re
import pandas as pd
from collections import Counter

docs = ["Кофе вкусный, но холодный", "Кофе горький, кофе холодный", "Холодный, но вкусный кофе"]
bags = [Counter(re.findall(r"[а-яё]+", d.lower())) for d in docs]
table = pd.DataFrame(bags).fillna(0).astype(int)
print(table[sorted(table.columns)])
```

**Что здесь происходит:**

- `Counter(токены)` — мешок одного отзыва: словарь «слово → сколько раз».
- `pd.DataFrame(список_словарей)` — каждый словарь стал строкой, ключи — столбцами. Слова, которых в отзыве нет, получились `NaN`.
- `.fillna(0).astype(int)` — «нет слова» значит 0 раз.
- `table[sorted(table.columns)]` — столбцы по алфавиту, как в таблице выше.

Каждый отзыв теперь — строка чисел одинаковой длины. С такой таблицей уже может работать любая модель sklearn.

::: quiz
Что именно теряется, когда отзыв превращают в мешок слов?

- [x] Порядок слов: «кофе вкусный, но дорого» и «дорого, но кофе вкусный» дают одинаковые строки таблицы
  > Мешок помнит только, какие слова и сколько раз встретились, но не где они стояли.
- [ ] Сколько раз встретилось слово — остаётся только «есть или нет»
  > Счёт сохраняется: у «Кофе горький, кофе холодный» в столбце «кофе» стоит 2.
- [ ] Редкие слова — в мешок попадают только самые частые
  > В мешке есть все слова словаря, просто у каждого отзыва большинство клеток — нули. Редкие слова выбрасывают отдельным решением.
- [ ] Связь чисел со словами — после превращения в числа уже не понять, какое слово стояло в столбце
  > Каждый столбец соответствует слову словаря, по таблице всегда видно, о каком слове речь.
:::

{{practice: bag}}

## Разберём вместе: слова, которые встретились один раз

Мы насчитали меньше 500 разных слов. Какие из них редкие и что это за слова? Это важный вопрос: каждое слово мешка — отдельный признак, и признак, который встретился один раз, модели почти бесполезен.

**План:** посчитать частоты всех слов → отобрать слова с частотой 1 → посмотреть на примеры.

```python
import re
from collections import Counter
import pandas as pd

r = pd.read_csv("reviews_text.csv")
words = Counter()
for text in r["text"]:
    words.update(re.findall(r"[а-яё]+", text.lower()))

once = sorted(w for w, n in words.items() if n == 1)
print("разных слов:", len(words), "| встретились один раз:", len(once))
print(once[:20])
```

**Что получилось:** почти половина словаря — слова, встретившиеся ровно один раз. И почти все они — опечатки («досавка», «зпомнил», «длго») или слова, склеившиеся из-за пропущенного пробела («быстродаже»). В настоящих отзывах редких слов ещё больше. Отсюда два практических вывода, которые пригодятся в уроке «Мешок слов и TF-IDF»: редкие слова часто выбрасывают из словаря (параметр `min_df`), а против опечаток помогают признаки из кусочков слов — буквенные n-граммы.

{{practice: hapax}}

## Практика

## task: tokenize | Токенизатор | warmup

Напишите функцию `tokenize(text)`, которая возвращает список слов из русских букв в нижнем регистре. Сохраните `t = tokenize("Кофе — ОТЛИЧНЫЙ, ёжики!!! 10/10")`.

### starter
```python
import re

```

### check
```python
f = need('tokenize')
assert f('Привет, Мир!') == ['привет', 'мир'], f'tokenize("Привет, Мир!") = {f("Привет, Мир!")}.'
assert list(need('t')) == ['кофе', 'отличный', 'ёжики'], f't = {need("t")}. Не забудьте букву ё и нижний регистр.'
```

### hint
Сначала нижний регистр, потом поиск всех последовательностей русских букв.

### hint
`re.findall(r"[а-яё]+", text.lower())`.

### solution
```python
import re

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

t = tokenize("Кофе — ОТЛИЧНЫЙ, ёжики!!! 10/10")
```

## task: clean | Нормализация текста | warmup

Напишите `normalize(text)`: перевести в нижний регистр, заменить «ё» на «е», а все символы, кроме русских букв и пробела, заменить пробелами; затем схлопнуть повторяющиеся пробелы в один и убрать пробелы по краям. Примените к `raw` — результат в `clean`.

### setup
```python
raw = "  Ёлки!!! Кофе —  ОТЛИЧНЫЙ,   ещё приду :) "
```

### starter
```python
import re

def normalize(text):
    ...

clean = normalize(raw)
print(repr(clean))
```

### check
```python
f = need('normalize')
assert need('clean') == 'елки кофе отличный еще приду', f'clean = {need("clean")!r}.'
assert f('Всё ОК, 10 из 10!') == 'все ок из', f'normalize("Всё ОК, 10 из 10!") = {f("Всё ОК, 10 из 10!")!r}.'
assert f('') == '', 'Пустая строка должна остаться пустой.'
```

### hint
Порядок шагов важен: сначала `lower()`, потом `replace("ё", "е")`, потом замена не-букв.

### hint
Всё, что не русская буква и не пробел: `re.sub(r"[^а-я ]", " ", text)` (после замены «ё» она в шаблоне уже не нужна). Схлопнуть пробелы: `re.sub(r" +", " ", text)`.

### hint
В конце — `.strip()`, чтобы убрать пробелы в начале и конце.

### solution
```python
import re

def normalize(text):
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^а-я ]", " ", text)
    return re.sub(r" +", " ", text).strip()

clean = normalize(raw)
print(repr(clean))
```

## task: vocab | Словарь отзывов | warmup

Посчитайте частоты всех слов во всех отзывах (`Counter`). Сохраните `n_words` — число разных слов, `total` — общее число словоупотреблений и `top5` — список пяти самых частых слов (без частот).

### starter
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import re as _re, pandas as _pd
from collections import Counter as _C
c = _C()
for t in _pd.read_csv('reviews_text.csv')['text']:
    c.update(_re.findall(r'[а-яё]+', t.lower()))
assert need('n_words') == len(c), f'n_words = {need("n_words")}, а нужно {len(c)}.'
assert need('total') == sum(c.values()), f'total = {need("total")}.'
assert list(need('top5')) == [w for w, _ in c.most_common(5)], f'top5 = {need("top5")}.'
```

### hint
Счётчик заводится один раз до цикла: `words = Counter()`, а в цикле по отзывам пополняется.

### hint
`words.update(список_токенов)` для каждого отзыва; всего — `sum(words.values())`.

### solution
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

words = Counter()
for text in r["text"]:
    words.update(re.findall(r"[а-яё]+", text.lower()))
n_words = len(words)
total = sum(words.values())
top5 = [w for w, _ in words.most_common(5)]
```

## task: p-stop | Удаление стоп-слов | warmup

Соберите код, который удаляет стоп-слова, но сохраняет отрицание «не» и переключатель «но» — по правилу из раздела выше.

### parsons
```python
import re
stop = {"и", "в", "с", "но", "не", "на"}
keep = {"не", "но"}
text = "Кофе не горячий, но с горечью"
tokens = [w for w in re.findall(r"[а-яё]+", text.lower()) if w not in stop - keep]
print(tokens)
```

### check
```python
assert _lines == ["['кофе', 'не', 'горячий', 'но', 'горечью']"], f'Сейчас: {_lines}.'
```

### hint
`stop - keep` — разность множеств: стоп-слова без «не» и «но».

### hint
Фильтр токенов — списковое выражение с условием `if w not in stop_clean`.

## task: neg-words | Слова плохих отзывов | base

Разделите отзывы на негативные (`rating <= 2`) и позитивные (`rating >= 4`). Посчитайте частоты слов в каждой группе. Сохраните `ne_share_neg` и `ne_share_pos` — долю отзывов с токеном «не» в каждой группе (3 знака) и `top_neg` — список из 10 слов, собранный так: идите по словам негативных отзывов от самых частых к редким и пропускайте те, что входят в 100 самых частых слов позитивных, пока не наберёте 10.

### starter
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
from collections import Counter as _C
r0 = _pd.read_csv('reviews_text.csv'); tk = lambda t: _re.findall(r'[а-яё]+', t.lower())
ng, ps = r0[r0['rating'] <= 2], r0[r0['rating'] >= 4]
sh = lambda d: round(float(d['text'].map(lambda t: 'не' in tk(t)).mean()), 3)
assert close(need('ne_share_neg'), sh(ng)) and close(need('ne_share_pos'), sh(ps)), f'ne_share_neg, ne_share_pos = {need("ne_share_neg")}, {need("ne_share_pos")}.'
cn, cp = _C(), _C()
for t in ng['text']: cn.update(tk(t))
for t in ps['text']: cp.update(tk(t))
top_p = {w for w, _ in cp.most_common(100)}
want = [w for w, _ in cn.most_common() if w not in top_p][:10]
assert list(need('top_neg')) == want, f'top_neg = {need("top_neg")}, а нужно {want}.'
```

### hint
Доля отзывов с «не»: `group["text"].map(lambda t: "не" in tokenize(t)).mean()`.

### hint
Пройдите по `counter_neg.most_common()` и берите слова, которых нет в множестве топ-100 позитивных, пока не наберётся 10.

### solution
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

neg = r[r["rating"] <= 2]
pos = r[r["rating"] >= 4]
ne_share_neg = round(float(neg["text"].map(lambda t: "не" in tokenize(t)).mean()), 3)
ne_share_pos = round(float(pos["text"].map(lambda t: "не" in tokenize(t)).mean()), 3)
c_neg, c_pos = Counter(), Counter()
for t in neg["text"]:
    c_neg.update(tokenize(t))
for t in pos["text"]:
    c_pos.update(tokenize(t))
top_pos = {w for w, _ in c_pos.most_common(100)}
top_neg = [w for w, _ in c_neg.most_common() if w not in top_pos][:10]
```

### explain
«Не» есть в двух из пяти плохих отзывов и лишь в 5 % хороших — на одном этом слове уже можно построить правило. В `top_neg` первыми идут «но» и «больше» — это не темы, а маркеры тональности: «вкусно, но…», «больше не приду». Дальше — слова, которые подсказывают темы жалоб: «вкуса нет», «холодный», «водянистый».

## task: bag | Мешок слов руками | plus

Постройте мешок слов для трёх отзывов: словарь `vocab` — отсортированный список всех слов трёх отзывов, и матрицу `bow` (список списков или массив 3 × len(vocab)), где в строке i, столбце j — сколько раз слово `vocab[j]` встречается в отзыве i. Сохраните также `same_bag` — `True`, если у отзывов 0 и 2 одинаковые мешки.

### starter
```python
import re
docs = ["Кофе вкусный, но дорого.",
        "Кофе горький, кофе холодный.",
        "Дорого, но кофе вкусный!"]

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import numpy as _np
v = ['вкусный', 'горький', 'дорого', 'кофе', 'но', 'холодный']
assert list(need('vocab')) == v, f'vocab = {need("vocab")}.'
b = _np.asarray(need('bow'))
assert b.tolist() == [[1, 0, 1, 1, 1, 0], [0, 1, 0, 2, 0, 1], [1, 0, 1, 1, 1, 0]], f'bow = {b.tolist()}.'
assert need('same_bag') == True, 'same_bag должно быть True — порядок слов в мешке теряется.'
```

### hint
Словарь — все разные слова всех отзывов по алфавиту; строка мешка — сколько раз каждое слово словаря встречается в отзыве.

### hint
`vocab = sorted({w for d in docs for w in tokenize(d)})`; строка мешка — `[tokens.count(w) for w in vocab]`.

### hint
`same_bag = bow[0] == bow[2]` — списки сравниваются поэлементно.

### solution
```python
import re
docs = ["Кофе вкусный, но дорого.",
        "Кофе горький, кофе холодный.",
        "Дорого, но кофе вкусный!"]

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

vocab = sorted({w for d in docs for w in tokenize(d)})
bow = []
for d in docs:
    tokens = tokenize(d)
    bow.append([tokens.count(w) for w in vocab])
same_bag = bow[0] == bow[2]
```

### explain
Отзывы 0 и 2 состоят из одних и тех же слов в разном порядке — и мешки у них одинаковые. Для тональности это обычно не страшно: «вкусно, но дорого» и «дорого, но вкусно» оба смешанные. А вот «не вкусно, а дёшево» и «вкусно, а не дёшево» мешок не различит — это и есть цена простоты. Частично помогают пары соседних слов (биграммы) — о них задача «Пары слов в плохих отзывах» ниже и урок «Мешок слов и TF-IDF».

## task: hapax | Редкие слова | base

Посчитайте частоты всех слов в отзывах (токенизатор `tokenize` — в заготовке). Сохраните `n_words` — размер словаря, `once` — отсортированный список слов, встретившихся ровно один раз, `share_once_vocab` — их долю среди **разных** слов словаря и `share_once_tokens` — их долю среди **всех** употреблений слов (обе доли — 4 знака).

### setup
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())
```

### starter
```python
from collections import Counter

words = Counter()

```

### check
```python
from collections import Counter as _C
r0, tk = need('r'), need('tokenize')
w = _C()
for t in r0['text']:
    w.update(tk(t))
o = sorted(k for k, v in w.items() if v == 1)
assert need('n_words') == len(w), f'n_words = {need("n_words")}.'
assert need('once', list) == o, f'В once должно быть {len(o)} слов, а сейчас {len(need("once"))}.'
assert close(need('share_once_vocab'), round(len(o) / len(w), 4), 0.00011), f'share_once_vocab = {need("share_once_vocab")}: доля слов-однодневок среди разных слов.'
assert close(need('share_once_tokens'), round(len(o) / sum(w.values()), 4), 0.00011), f'share_once_tokens = {need("share_once_tokens")}: доля однодневок среди всех употреблений.'
```

### hint
Счётчик пополняется в цикле по отзывам: `words.update(tokenize(text))`.

### hint
Слова с частотой 1: `[w for w, n in words.items() if n == 1]` — и `sorted(...)`. Все употребления — `sum(words.values())`.

### hint
`share_once_vocab = round(len(once) / len(words), 4)`; `share_once_tokens = round(len(once) / sum(words.values()), 4)`.

### solution
```python
from collections import Counter

words = Counter()
for text in r["text"]:
    words.update(tokenize(text))
n_words = len(words)
once = sorted(w for w, n in words.items() if n == 1)
share_once_vocab = round(len(once) / n_words, 4)
share_once_tokens = round(len(once) / sum(words.values()), 4)
print(n_words, len(once), share_once_vocab, share_once_tokens)
```

### explain
Почти половина словаря — слова-однодневки (227 из 491, 0.4623), но в тексте они занимают лишь около процента всех слов (0.0118). Это типичная картина для любых текстов (закон Ципфа): немного слов встречаются постоянно, а длинный хвост — очень редко. Для модели хвост — в основном шум и опечатки; его обрезают, оставляя слова, которые встречаются хотя бы в нескольких отзывах. В уроке «Мешок слов и TF-IDF» это делает один параметр `min_df`.

## task: bigrams | Пары слов в плохих отзывах | plus

Мешок слов теряет порядок, но пары соседних слов (**биграммы**) его частично сохраняют: «не понравился» — одна биграмма. Для каждого отзыва соберите множество его биграмм (`zip(tokens, tokens[1:])`). Посчитайте для каждой биграммы долю плохих (`rating <= 3`) и долю хороших отзывов, где она встречается. Сохраните `top_bad` — список из 5 биграмм (кортежей) с наибольшей разностью «доля в плохих − доля в хороших» (по убыванию), и `diff_top` — эту разность для первой из них (3 знака).

### setup
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())
```

### starter
```python
from collections import Counter

bad = r["rating"] <= 3

```

### check
```python
from collections import Counter as _C
r0, tk = need('r'), need('tokenize')
b0 = r0['rating'] <= 3
cb, cg = _C(), _C()
for t, isb in zip(r0['text'], b0):
    tok = tk(t); bg = set(zip(tok, tok[1:]))
    (cb if isb else cg).update(bg)
nb, ng = int(b0.sum()), int((~b0).sum())
d = {k: cb[k] / nb - cg[k] / ng for k in set(cb) | set(cg)}
w = sorted(d, key=lambda k: (-d[k], k))[:5]
got = [tuple(x) for x in need('top_bad', list)]
assert len(got) == 5, 'top_bad — 5 биграмм.'
assert set(got) == set(w) or got[:3] == w[:3], f'top_bad = {got}, а нужно {w}.'
assert close(need('diff_top'), round(d[w[0]], 3), 0.0011), f'diff_top = {need("diff_top")}.'
```

### hint
Множество биграмм отзыва: `set(zip(tokens, tokens[1:]))` — `set`, чтобы биграмма, встретившаяся в отзыве дважды, считалась один раз.

### hint
Два счётчика: для плохих и для хороших отзывов. Доля в плохих — `count_bad[bg] / число_плохих`; для биграмм, которых нет в одном из счётчиков, `Counter` вернёт 0.

### hint
```python
diff = {bg: cb[bg] / nb - cg[bg] / ng for bg in set(cb) | set(cg)}
top_bad = sorted(diff, key=lambda k: (-diff[k], k))[:5]
```

### solution
```python
from collections import Counter

bad = r["rating"] <= 3
cb, cg = Counter(), Counter()
for text, is_bad in zip(r["text"], bad):
    tokens = tokenize(text)
    bgs = set(zip(tokens, tokens[1:]))
    (cb if is_bad else cg).update(bgs)
nb, ng = int(bad.sum()), int((~bad).sum())
diff = {bg: cb[bg] / nb - cg[bg] / ng for bg in set(cb) | set(cg)}
top_bad = sorted(diff, key=lambda k: (-diff[k], k))[:5]
diff_top = round(diff[top_bad[0]], 3)
print(top_bad, diff_top)
```

### explain
Наверху — «не приду», «больше не», «не советую», «вкуса нет»: почти все сильные биграммы содержат отрицание. Каждая из них встречается в плохих отзывах примерно на 5–9 процентных пунктов чаще, чем в хороших. Слово «не» само по себе тоже сильный сигнал (задача «Слова плохих отзывов»), но биграмма уточняет, *что именно* отрицается: «не советую» — однозначно плохо, а «не пожалела» было бы хорошо. Биграммы — первый шаг от мешка слов к учёту порядка; в уроке «Мешок слов и TF-IDF» их включает один параметр `ngram_range=(1, 2)`.

## task: rule | Правило «не» | star

Простейший классификатор тональности: «отзыв негативный, если в нём есть токен "не" **или** "но"». Посчитайте на всех отзывах (негативный — `rating <= 3`) долю правильных ответов `acc_rule` и F1 для класса «негативный» `f1_rule` (3 знака). Затем то же для правила только по «не» — `acc_ne`, `f1_ne`.

### starter
```python
import re
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
from sklearn.metrics import accuracy_score as _acc, f1_score as _f1
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
tk = r0['text'].map(lambda t: set(_re.findall(r'[а-яё]+', t.lower())))
p1 = tk.map(lambda s: int('не' in s or 'но' in s)); p2 = tk.map(lambda s: int('не' in s))
for k, v in [('acc_rule', _acc(y0, p1)), ('f1_rule', _f1(y0, p1)), ('acc_ne', _acc(y0, p2)), ('f1_ne', _f1(y0, p2))]:
    assert close(need(k), round(v, 3), 0.002), f'{k} = {need(k)}, а нужно {round(v, 3)}.'
```

### hint
Правило: «плохой отзыв», если среди токенов есть «не» или «но». Сравните прогноз с `(r["rating"] <= 3).astype(int)`.

### hint
Прогноз — Series из 0/1: `r["text"].map(lambda t: int("не" in tokenize(t) or "но" in tokenize(t)))`.

### solution
```python
import re
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

tokens = r["text"].map(lambda t: set(tokenize(t)))
rule = tokens.map(lambda s: int("не" in s or "но" in s))
only_ne = tokens.map(lambda s: int("не" in s))
acc_rule, f1_rule = round(accuracy_score(y, rule), 3), round(f1_score(y, rule), 3)
acc_ne, f1_ne = round(accuracy_score(y, only_ne), 3), round(f1_score(y, only_ne), 3)
```

### explain
Правило из двух слов уже даёт около 80 % правильных ответов. Добавление «но» ловит смешанные отзывы («вкусно, но дорого»). Это ориентир, который модель в следующих уроках должна уверенно побить.
