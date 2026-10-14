---
title: "Леммы и словарь исключений"
lead: "«Сырники», «сырников» и «сырником» для модели — три разных слова. Сводим формы слова вместе: сначала грубо — обрезанием окончаний, потом по-настоящему — лемматизатором pymorphy3. Смотрим, где лемматизатор ошибается на словах меню, и чиним это словарём исключений."
files: [reviews_text.csv, review_lemmas.csv]
recap:
  - "Лемматизация приводит слово к начальной форме (сырники → сырник). Для русского — библиотеки pymorphy3 или natasha; в браузере их нет, поэтому используем стемминг или заранее посчитанную таблицу лемм `review_lemmas.csv`."
  - "pymorphy3 знает слова из словаря (привезли → привезти, лучший → хороший), а лемму незнакомого слова угадывает по окончанию и на меню ошибается (капучино → капучиный). Частые незнакомые слова просматривают и правят словарём исключений на уровне лемм."
  - "Лемму считают один раз на разное слово и кэшируют: разных слов — тысячи, словоупотреблений — миллионы."
  - "Стемминг — обрезание слова до первых n букв: быстро и без словаря, но склеивает разные слова с общим началом (приветливые и привезли) и не склеивает формы, где меняется буква внутри основы (привезли — привёз: «е» и «ё» разные буквы)."
---

В уроке «Текст как данные: очистка и токены» мы разбили отзывы на токены и посчитали частоты: во всех отзывах 491 разное слово. Многие из них — формы одного и того же слова. Здесь сведём их вместе.

## Формы слов

«Сырники», «сырников», «сырником» — одно слово в разных формах. Для модели это три разных признака, и каждый встречается реже. **Лемматизация** приводит слово к начальной форме — лемме: сырники → сырник, привезли → привезти. Для русского языка этим занимаются библиотеки `pymorphy3` и `natasha`; на своём компьютере ставятся через `uv add pymorphy3`.

```python static
import pymorphy3
morph = pymorphy3.MorphAnalyzer()
print([morph.parse(w)[0].normal_form for w in ["сырники", "привезли", "холодный", "курьером"]])
# ['сырник', 'привезти', 'холодный', 'курьер']
```

В браузере `pymorphy3` нет, поэтому в задачах используем упрощение — **стемминг** (обрезание окончаний): оставить первые 5–6 букв слова. Как это выглядит:

| Слово | Первые 5 букв | Первые 6 букв |
|---|---|---|
| сырники, сырников | сырни | сырник |
| курьер, курьером | курье | курьер |
| холодный, холодная | холод | холодн |
| приветливые, привезли | приве | привет / привез |

::: figure stem-vs-lemma
Семь слов из отзывов: слева — основа из первых пяти букв, справа — лемма из `review_lemmas.csv`. Стемминг склеивает чужие слова («приветливые» и «привезли») и не склеивает формы одного («привезли» и «привёз»); лемматизатор сводит даже «лучший» к «хороший».
:::

Видно и пользу (формы одного слова слились), и вред (при 5 буквах «приветливые» и «привезли» тоже слились, хотя слова разные). А «привезли» и «привёз» не слились ни при 5, ни при 6 буквах: токенизатор сохраняет «ё», и пятая буква у них разная. Это грубо (при n = 4 «кофейня» превратилась бы в «кофе» и слилась с напитком), но часто работает и показывает идею: свести формы одного слова вместе.

{{practice: stem-pairs, stem}}

## Лемматизация по-настоящему: pymorphy3

Стемминг режет вслепую. **Лемматизатор** знает русскую грамматику: у него есть словарь (для `pymorphy3` — словарь OpenCorpora, около 390 тысяч лемм) и правила склонения и спряжения. Для каждого слова он перебирает возможные разборы и возвращает начальную форму.

::: sql
Лемматизация похожа на справочник-маппинг в хранилище: `JOIN` таблицы «слово → лемма» к токенам и `GROUP BY lemma` вместо `GROUP BY word`. Разница в том, что справочник для `pymorphy3` построен по грамматике, а для слов, которых в нём нет, лемма угадывается по окончанию — как если бы `LEFT JOIN` не нашёл строку и подставил «похожую».
:::

Игрушечный пример: что делает лемматизатор с четырьмя словами из отзывов.

| слово | разбор | лемма | откуда |
|---|---|---|---|
| привезли | глагол, прошедшее время, мн. число | привезти | из словаря |
| лучший | прилагательное, превосходная степень | хороший | из словаря — даже другая основа |
| капучино | слова нет в словаре; окончание как у «смешно» | капучиный | догадка — неверная |
| бариста | слова нет; окончание как у «артиста» | барист | догадка — неверная |

Первые две строки стеммингу недоступны: «лучший» и «хороший» не имеют общего начала. Последние две — цена словарного подхода: названия напитков и профессий из кофейни словарь не знает.

`pymorphy3` в браузере не работает (ему нужны файлы словаря), поэтому мы один раз прогнали его по всем словам отзывов и сохранили результат в таблицу `review_lemmas.csv`. На своём компьютере то же делается так:

```python static
# uv add pymorphy3
import pymorphy3
morph = pymorphy3.MorphAnalyzer()
p = morph.parse("привезли")[0]          # самый вероятный разбор
print(p.normal_form, p.tag.POS, round(p.score, 3), morph.word_is_known("привезли"))
# привезти VERB 1.0 True
print(morph.parse("капучино")[0].normal_form, morph.word_is_known("капучино"))
# капучиный False
```

Полный разбор — с несколькими вариантами разбора, кэшем и лемматизацией в конвейере sklearn — в локальном блокноте [ch13-pymorphy3.ipynb](../notebooks/extra/ch13-pymorphy3.ipynb) (в архиве курса он лежит в папке `notebooks/extra/`, данные берёт из папки `data` курса; нужна библиотека `pymorphy3`).

Теперь посмотрим, как таблица лемм меняет словарь отзывов:

```python
import re
import pandas as pd

r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
print(lem.head(4))

to_lemma = dict(zip(lem["word"], lem["lemma"]))          # словарь «слово → лемма»
tokens = [w for t in r["text"] for w in re.findall(r"[а-яё]+", t.lower())]
print("слов:", len(set(tokens)),
      "| лемм:", len({to_lemma[w] for w in tokens}),
      "| основ по 5 букв:", len({w[:5] if len(w) > 5 else w for w in set(tokens)}))
print(r.loc[0, "text"])
print(" ".join(to_lemma[w] for w in re.findall(r"[а-яё]+", r.loc[0, "text"].lower())))
```

**Что здесь происходит:**

- `review_lemmas.csv` — по строке на каждое из 491 разных слов отзывов: `lemma` — начальная форма, `pos` — часть речи, `known` — есть ли слово в словаре (1) или лемма угадана (0), `score` — уверенность разбора, `count` — сколько раз слово встречается.
- `score` — доля самого вероятного разбора среди всех разборов слова. У несклоняемых слов разборов много (форма «кофе» одинакова во всех падежах, и каждый падеж — отдельный разбор), поэтому у «кофе» `score` всего 0.214, хотя лемма верная. Низкий `score` значит «форма неоднозначна», а не «лемма неверна»; о неверной лемме говорит `known = 0`.
- `dict(zip(lem["word"], lem["lemma"]))` — превращаем две колонки в словарь, чтобы заменять слова за одно обращение.
- Три числа — размер словаря: исходных слов, лемм и «основ» по пяти буквам.
- Последние две строки — первый отзыв до и после лемматизации.

**Что получилось:** 491 слово сводится к 450 леммам — лемматизатор склеивает только формы одного слова и потому осторожнее стемминга (377 основ: тот склеивает и чужие слова). В отзыве «дороговато для такого кофе» превращается в «дороговатый для такой кофе»: грамматика стёрта, смысл для модели остался.

::: warn Типичные ошибки
- **Верить лемме незнакомого слова.** У 240 из 491 слова `known = 0`: это опечатки синтетических отзывов и слова меню. Для них лемма — догадка: «капучино» → «капучиный», «латте» → «латта». Частые незнакомые слова надо просмотреть и поправить своим словарём исключений (задача ниже).
- **Лемматизировать каждый раз заново.** `morph.parse` — самая медленная часть: на миллионе отзывов это минуты. Разных слов же — тысячи, поэтому лемму считают один раз на слово и кэшируют (`functools.lru_cache` или таблица, как здесь).
- **Сверять стоп-слова и токены в разном виде.** Если список стоп-слов записан леммами («быть», «этот»), а удаляете вы их из исходных токенов, то «был» и «этого» останутся в тексте. Список и токены должны быть в одном виде: список в леммах — удаляйте стоп-слова после лемматизации, список словоформ — до.
:::

{{practice: lemma-text, lemmas, lemma-top, lemma-fix}}

## Практика

## task: stem-pairs | Где стемминг ошибается | warmup

Напишите функцию `stem(word, n)`: если слово длиннее `n` букв — оставить первые `n`, иначе вернуть слово как есть. Для списка `words` из заготовки сохраните `n5` и `n6` — сколько **разных** основ получается при `n = 5` и при `n = 6`, и `glued5` — `True`, если «приветливые» и «привезли» при `n = 5` дают одну основу.

### starter
```python
words = ["сырники", "сырников", "сырником", "приветливые", "привезли", "привёз", "холодный", "холодная"]

```

### check
```python
f = need('stem')
assert f('кофейня', 4) == 'кофе' and f('кофе', 5) == 'кофе', f'stem("кофейня", 4) = {f("кофейня", 4)!r}, stem("кофе", 5) = {f("кофе", 5)!r}: длинное слово обрезается, короткое остаётся как есть.'
ws = ["сырники", "сырников", "сырником", "приветливые", "привезли", "привёз", "холодный", "холодная"]
st = lambda w, n: w[:n] if len(w) > n else w
assert need('n5') == len({st(w, 5) for w in ws}), f'n5 = {need("n5")}: число разных основ — длина множества.'
assert need('n6') == len({st(w, 6) for w in ws}), f'n6 = {need("n6")}.'
assert need('glued5') == True, 'glued5: сравните stem("приветливые", 5) и stem("привезли", 5).'
```

### hint
Разные основы — множество: `{stem(w, 5) for w in words}`, его размер — `len(...)`.

### hint
`glued5 = stem("приветливые", 5) == stem("привезли", 5)`.

### solution
```python
words = ["сырники", "сырников", "сырником", "приветливые", "привезли", "привёз", "холодный", "холодная"]

def stem(word, n):
    return word[:n] if len(word) > n else word

n5 = len({stem(w, 5) for w in words})
n6 = len({stem(w, 6) for w in words})
glued5 = stem("приветливые", 5) == stem("привезли", 5)
print(n5, n6, glued5)
```

### explain
При пяти буквах восемь слов дают 4 основы: три «сырника» и два «холодных» слились правильно, а «приветливые» и «привезли» — ошибочно. При шести буквах основ 5: «привет» и «привез» разошлись, формы «сырника» и «холодного» по-прежнему вместе. «Привёз» отдельно в обоих случаях — из-за «ё». Длина обрезания — компромисс: короче — больше чужих слов слипается, длиннее — больше форм одного слова расходится.

## task: stem | Стемминг обрезанием | base

Напишите функцию `stem(word, n=5)`: если слово длиннее `n` букв — оставить первые `n`, иначе вернуть как есть. Посчитайте число разных слов во всех отзывах до (`n_raw`) и после стемминга (`n_stem`). Сохраните `merged` — список слов, которые после стемминга совпали с `stem("курьер")`, в алфавитном порядке.

### starter
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
r0 = _pd.read_csv('reviews_text.csv'); tk = lambda t: _re.findall(r'[а-яё]+', t.lower())
st = lambda w, n=5: w[:n] if len(w) > n else w
allw = {w for t in r0['text'] for w in tk(t)}
f = need('stem')
assert f('кофейня') == 'кофей' and f('кофе') == 'кофе', 'stem: обрезать до 5 букв, короткие слова не трогать.'
assert need('n_raw') == len(allw) and need('n_stem') == len({st(w) for w in allw}), f'n_raw, n_stem = {need("n_raw")}, {need("n_stem")}.'
assert list(need('merged')) == sorted(w for w in allw if st(w) == st('курьер')), f'merged = {need("merged")}.'
```

### hint
Множество всех слов: `{w for t in r["text"] for w in tokenize(t)}`.

### hint
Обрезанное слово — `w[:5]`. Сколько разных «основ» — длина множества `{w[:5] for w in all_words}`.

### solution
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

def stem(word, n=5):
    return word[:n] if len(word) > n else word

all_words = {w for t in r["text"] for w in tokenize(t)}
n_raw = len(all_words)
n_stem = len({stem(w) for w in all_words})
merged = sorted(w for w in all_words if stem(w) == stem("курьер"))
```

### explain
Обрезание до 5 букв склеивает «курьер» с опечаткой «курье» — это полезно. Но заодно в ту же группу попал «курьервежливый» — два слова, склеенные опечаткой без пробела, — и могли бы попасть разные слова с общим началом. Для настоящей работы с русским текстом лучше лемматизация.

## task: lemma-text | Отзыв в леммах | warmup

Соберите из таблицы `review_lemmas.csv` словарь `to_lemma` («слово → лемма») и напишите функцию `lemmatize(text)`: разбить текст на токены и вернуть строку из их лемм через пробел. Сохраните `first` — первый отзыв (`r.loc[0, "text"]`) в леммах.

### starter
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
f = need('lemmatize')
got = f('Бариста были приветливые')
assert got == 'барист быть приветливый', f'lemmatize("Бариста были приветливые") = {got!r}, а нужно \'барист быть приветливый\'.'
assert need('first') == 'приготовить быстро даже в очередь но дороговатый для такой кофе', f'first = {need("first")!r}.'
```

### hint
Словарь — `dict(zip(lem["word"], lem["lemma"]))`. В таблице есть все слова отзывов, поэтому `to_lemma[w]` не упадёт.

### hint
`" ".join(to_lemma[w] for w in tokenize(text))`.

### solution
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

to_lemma = dict(zip(lem["word"], lem["lemma"]))

def lemmatize(text):
    return " ".join(to_lemma[w] for w in tokenize(text))

first = lemmatize(r.loc[0, "text"])
print(first)
```

### explain
Грамматика ушла («дороговато для такого кофе» → «дороговатый для такой кофе»), смысл для модели остался. В проверочной фразе видно и ошибку: «бариста» стала «барист» — это лемма-догадка незнакомого слова, её чинят словарём исключений (задача «Исключения для слов меню»).

## task: lemmas | Словарь лемм | base

Размеры словаря до и после лемматизации (491 / 450 / 377) мы уже видели в теории. Теперь посмотрим, сколько работы лемматизатор сделал и насколько ему можно верить. Таблица `review_lemmas.csv` хранит лемму для каждого слова отзывов. Превратите её в словарь `to_lemma` («слово → лемма») и разбейте все отзывы на токены. Сохраните:

- `n_changed` — сколько **разных** слов отзывов лемматизатор изменил (лемма не совпадает с самим словом);
- `share_known` — долю **словоупотреблений** (каждого токена с повторами), которые есть в словаре pymorphy3 (`known == 1`), — 3 знака.

### starter
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
r0 = _pd.read_csv('reviews_text.csv'); l0 = _pd.read_csv('review_lemmas.csv')
tk = [w for t in r0['text'] for w in _re.findall(r'[а-яё]+', t.lower())]
m = dict(zip(l0['word'], l0['lemma'])); kn = dict(zip(l0['word'], l0['known']))
tl = need('to_lemma', dict)
assert tl.get('привезли') == 'привезти' and len(tl) == len(m), f'to_lemma: в словаре {len(tl)} слов, а в таблице {len(m)}. Соберите его из колонок word и lemma.'
nc = sum(1 for w in set(tk) if m[w] != w)
assert need('n_changed') == nc, f'n_changed = {need("n_changed")}, а нужно {nc}. Считайте разные слова (set), а не все токены с повторами.'
w = round(sum(kn[x] for x in tk) / len(tk), 3)
assert close(need('share_known'), w, 0.0015), f'share_known = {need("share_known")}. Доля считается по всем токенам с повторами, а не по разным словам.'
```

### hint
Сначала список всех токенов с повторами: `tokens = [w for t in r["text"] for w in tokenize(t)]`. Разные слова — `set(tokens)`.

### hint
Словарь — `dict(zip(lem["word"], lem["lemma"]))`. Изменённые слова — `sum(1 for w in set(tokens) if to_lemma[w] != w)`. Для `share_known` сделайте второй словарь из колонки `known`.

### hint
```python
known = dict(zip(lem["word"], lem["known"]))
share_known = round(sum(known[w] for w in tokens) / len(tokens), 3)
```

### solution
```python
import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

tokens = [w for t in r["text"] for w in tokenize(t)]
to_lemma = dict(zip(lem["word"], lem["lemma"]))
known = dict(zip(lem["word"], lem["known"]))

n_changed = sum(1 for w in set(tokens) if to_lemma[w] != w)
share_known = round(sum(known[w] for w in tokens) / len(tokens), 3)
print(n_changed, share_known)
```

### explain
Лемматизатор изменил 269 из 491 разного слова — больше половины словаря стоит не в начальной форме. Но склеились из них немногие: 491 слово дало 450 лемм. При этом почти половина **разных** слов незнакома словарю, а среди **словоупотреблений** незнакомых меньше 5 % (`share_known` около 0.954): незнакомые слова — в основном редкие опечатки. Если бы вы посчитали долю по разным словам, получили бы около 0.51 и решили, что лемматизатор бесполезен, — это частая ошибка «уникальные против всех».

## task: lemma-top | Частые леммы плохих отзывов | base

Посчитайте частоты **лемм** в плохих отзывах (`rating <= 3`, как везде в главе). Сохраните `top10` — список 10 самых частых лемм, `n_byt` — сколько раз встречается лемма «быть» и `forms_byt` — отсортированный список разных слов плохих отзывов, которые лемматизатор свёл к «быть».

### starter
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
to_lemma = dict(zip(lem["word"], lem["lemma"]))

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
from collections import Counter as _C
r0 = _pd.read_csv('reviews_text.csv'); l0 = _pd.read_csv('review_lemmas.csv')
m = dict(zip(l0['word'], l0['lemma']))
tk = [w for t in r0.loc[r0['rating'] <= 3, 'text'] for w in _re.findall(r'[а-яё]+', t.lower())]
c = _C(m[w] for w in tk)
assert list(need('top10')) == [k for k, _ in c.most_common(10)], f'top10 = {need("top10")}. Считайте леммы только плохих отзывов (rating <= 3).'
assert need('n_byt') == c['быть'], f'n_byt = {need("n_byt")}, а нужно {c["быть"]}.'
fb = sorted({w for w in tk if m[w] == 'быть'})
assert list(need('forms_byt')) == fb, f'forms_byt = {need("forms_byt")}, а нужно {fb}.'
```

### hint
Токены плохих отзывов: `[w for t in r.loc[r["rating"] <= 3, "text"] for w in tokenize(t)]`. Леммы — `to_lemma[w]` для каждого токена, счётчик — `Counter(...)`.

### hint
Формы «быть»: `sorted({w for w in tokens if to_lemma[w] == "быть"})` — множество, чтобы каждое слово попало один раз.

### solution
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
to_lemma = dict(zip(lem["word"], lem["lemma"]))

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

tokens = [w for t in r.loc[r["rating"] <= 3, "text"] for w in tokenize(t)]
c = Counter(to_lemma[w] for w in tokens)
top10 = [l for l, _ in c.most_common(10)]
n_byt = c["быть"]
forms_byt = sorted({w for w in tokens if to_lemma[w] == "быть"})
print(top10, n_byt, forms_byt)
```

### explain
После лемматизации «быть» поднимается на четвёртое место (216 употреблений): по отдельности «были», «был» и «было» стояли ниже, а вместе обогнали предлоги. Так же «приложение» и «приложении» вместе дают лемму «приложение» (147) — она попадает в десятку, хотя по словам её там нет. Среди форм «быть» есть и ошибка: одинокое «е» — опечатка в «Больше е приду» (пропущена буква «н»), которую лемматизатор принял за форму «быть». Отрицание при этом потерялось: опечатки бьют не только по словарю, но и по тональности.

## task: lemma-fix | Исключения для слов меню | plus

Лемматизатор угадывает лемму незнакомого слова по окончанию и на словах меню ошибается. Найдите подозрительные слова: незнакомые словарю (`known == 0`) и частые (`count >= 30`). Сохраните их список `suspects` по убыванию `count`. Затем примените к **леммам** поправки `fixes` из заготовки (если лемма есть в `fixes`, заменить её) и посчитайте по всем токенам отзывов: `n_barista` — сколько раз встречается лемма `"бариста"` после поправки, `top_drink` — самая частая из лемм `"кофе"`, `"капучино"`, `"латте"`, `"раф"` после поправки.

### starter
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
fixes = {"капучиный": "капучино", "латта": "латте", "барист": "бариста", "флэта": "флэт"}

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
from collections import Counter as _C
r0 = _pd.read_csv('reviews_text.csv'); l0 = _pd.read_csv('review_lemmas.csv')
fx = {"капучиный": "капучино", "латта": "латте", "барист": "бариста", "флэта": "флэт"}
s = l0[(l0['known'] == 0) & (l0['count'] >= 30)].sort_values('count', ascending=False)['word'].tolist()
assert list(need('suspects')) == s, f'suspects = {need("suspects")}. Отбор: known == 0 и count >= 30, порядок — по убыванию count.'
m = dict(zip(l0['word'], l0['lemma']))
c = _C(fx.get(m[w], m[w]) for t in r0['text'] for w in _re.findall(r'[а-яё]+', t.lower()))
assert need('n_barista') == c['бариста'], f'n_barista = {need("n_barista")}, а нужно {c["бариста"]}. Поправку применяют к лемме, а не к слову: под «барист» попадают и «бариста», и опечатка «барист».'
d = max(['кофе', 'капучино', 'латте', 'раф'], key=lambda k: c[k])
assert need('top_drink') == d, f'top_drink = {need("top_drink")!r}. Посчитайте леммы после поправки и сравните четыре напитка.'
```

### hint
Отбор строк — маской `(lem["known"] == 0) & (lem["count"] >= 30)`, затем `sort_values("count", ascending=False)` и колонка `word` списком.

### hint
Лемма с поправкой для слова `w`: сначала `l = to_lemma[w]`, потом `fixes.get(l, l)` — если леммы нет среди ключей, `get` вернёт её саму.

### hint
```python
to_lemma = dict(zip(lem["word"], lem["lemma"]))
c = Counter(fixes.get(to_lemma[w], to_lemma[w]) for t in r["text"] for w in tokenize(t))
n_barista = c["бариста"]
top_drink = max(["кофе", "капучино", "латте", "раф"], key=lambda d: c[d])
```

### solution
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
fixes = {"капучиный": "капучино", "латта": "латте", "барист": "бариста", "флэта": "флэт"}

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

suspects = (lem[(lem["known"] == 0) & (lem["count"] >= 30)]
            .sort_values("count", ascending=False)["word"].tolist())

to_lemma = dict(zip(lem["word"], lem["lemma"]))
c = Counter(fixes.get(to_lemma[w], to_lemma[w]) for t in r["text"] for w in tokenize(t))
n_barista = c["бариста"]
top_drink = max(["кофе", "капучино", "латте", "раф"], key=lambda d: c[d])
print(suspects, n_barista, top_drink, c["кофе"], c["капучино"])
```

### explain
В подозрительных — семь слов, и все объяснимы: шесть — меню и профессия (капучино, бариста, латте, флэт, круассаны, круассан), одно — обычный глагол «начислились» (про бонусы), которого нет в словаре, но лемма «начислиться» угадана верно. Круассаны в `fixes` не нужны: лемма «круассан» угадана верно, хотя слова нет в словаре. Поправка на уровне **лемм** ловит все формы сразу: «бариста» и опечатка «барист» дают 146 упоминаний. Если бы вы исправляли отдельные слова (`{"бариста": "бариста"}`), опечатка «барист» осталась бы отдельной леммой. Без поправок «капучино» превращалось в прилагательное «капучиный», и в отчёте о напитках этого слова не было бы вовсе; после поправки видно, что капучино упоминают реже кофе вообще, но чаще латте и рафа. Словарь исключений — обычная практика: его ведут рядом с кодом и пополняют, когда в отзывах появляются новые позиции меню.
