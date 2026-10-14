---
title: "Разметка текстов языковой моделью"
lead: "Большая языковая модель размечает отзывы по описанию, без обучающих примеров. Разбираем, как написать инструкцию с закрытым списком меток, превратить ответ-строку в данные и проверить разметку на выборке с известными ответами, — и как запустить небольшую модель у себя на компьютере в LM Studio."
files: [reviews_text.csv, reviews_new.csv]
recap:
  - "LLM размечает тексты по инструкции без обучения (zero-shot). Ответ — строго JSON из фиксированных меток, и его обязательно проверяют на размеченной выборке."
  - "Небольшую LLM можно запустить у себя в LM Studio: отзывы не уходят во внешний сервис, но модель слабее облачной — её проверяют на размеченной выборке так же."
  - "Доля верных на 200 отзывах имеет погрешность около ±5 п. п. (±2 · √(p(1 − p)/n)); сравнивать LLM с обученной моделью нужно на одних и тех же отзывах, по числу случаев, где права только одна."
---

Разметку языковой моделью проверяют так же, как разметку людьми в уроке «Качество разметки: голосование, каппа, золотой набор»: на выборке с известными ответами, с матрицей ошибок.

## Разметка большой языковой моделью

Большая языковая модель (LLM) умеет выполнить задачу по описанию, без обучающих примеров — это называют **zero-shot**. Для аналитика это значит: можно разметить тысячу отзывов по темам, которых не было в исходных данных, за минуты. Но ответ модели — текст, и его нужно превратить в данные.

```python static
# uv add anthropic   (или клиент вашего провайдера — схема та же)
import json
import anthropic

client = anthropic.Anthropic()          # ключ берётся из переменной окружения ANTHROPIC_API_KEY
MODEL = "..."                           # имя модели из документации провайдера

PROMPT = """Ты размечаешь отзывы о кофейнях.
Верни ТОЛЬКО JSON вида {"sentiment": ..., "topic": ...}, без пояснений.
sentiment: "positive" или "negative".
topic: одно из "кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера".

Отзыв: """

def label(text):
    msg = client.messages.create(
        model=MODEL, max_tokens=50, temperature=0,
        messages=[{"role": "user", "content": PROMPT + text}],
    )
    return msg.content[0].text            # строка — её ещё надо разобрать

print(label("Курьер опоздал на сорок минут, кофе остыл."))
```

**Что здесь происходит:**

- `anthropic.Anthropic()` — клиент API; ключ берётся из переменной окружения, в коде его не пишут.
- `PROMPT` — инструкция: что сделать, в каком формате ответить и какие метки допустимы. Текст отзыва дописывается в конец.
- `messages.create(...)` — один запрос к модели; `max_tokens=50` — ответ короткий (нам нужен только JSON), `temperature=0` — минимум случайности.
- `msg.content[0].text` — текст ответа. Это **строка**: в ней может оказаться не только JSON, поэтому её ещё нужно разобрать и проверить (задача «Разбор ответов LLM»).

::: figure llm-label-flow
Разметка LLM как конвейер: инструкция с закрытым списком меток → ответ-строка → разбор JSON → проверка меток. Ответы, не прошедшие разбор или проверку, — отдельная кучка, а качество меряют на выборке с известными метками до разметки всего.
:::

Правила, без которых разметка LLM превращается в лотерею:

1. **Закрытый список меток.** Перечислите допустимые значения прямо в инструкции и проверяйте каждый ответ: модель может придумать «парковку» или «нейтрально».
2. **Машиночитаемый формат.** Просите JSON и разбирайте его кодом; всё, что не разобралось, — отдельная кучка «не удалось», а не молча выброшенные строки.
3. **`temperature=0`.** Меньше случайности — ответы воспроизводимы.
4. **Проверка на разметке.** Прежде чем размечать всё, прогоните 100–200 текстов с известными метками и посчитайте точность и матрицу ошибок — ровно как для любой модели в этом курсе.
5. **Стоимость и данные.** Оплата — за токены (куски слов), отдельно за входные (инструкция + отзыв) и выходные (ответ): прикиньте объём заранее. Точное число токенов знает только токенизатор провайдера; для прикидки по русскому тексту можно брать около одного токена на три символа и потом сверить со счётом за пробный прогон. И не отправляйте внешнему сервису персональные данные клиентов без разрешения.

::: deep
Почему бы не размечать всё LLM? Она медленнее и дороже обученной модели на порядки, а результат зависит от версии модели у провайдера. Частая схема: LLM размечает несколько сотен примеров, человек проверяет выборку, а на этой разметке обучают быстрый TF-IDF или эмбеддинги + логрегрессию, которые и работают в проде.
:::

::: quiz
LLM разметила 2000 отзывов по темам. Что сделать, прежде чем использовать разметку в отчёте?

- [x] Проверить на выборке, размеченной человеком, и отдельно посчитать ответы, которые не разобрались или вышли за список тем
  > LLM ошибается и иногда выдумывает темы. Без проверки качество разметки неизвестно.
- [ ] Ничего: LLM понимает текст лучше классификатора
  > Часто понимает, но не всегда — и мы не знаем, где именно ошибки.
- [ ] Переразметить всё ещё раз и взять большинство
  > Это повышает стабильность, но не заменяет сверки с человеком.
- [ ] Удалить отзывы, где LLM сомневалась
  > Тогда отчёт станет смещённым: сложные отзывы пропадут.
:::

**Как сравнивать LLM с обученной моделью.** Проверка на 200 отзывах даёт долю верных с погрешностью. Для доли $p$ на $n$ отзывах стандартная ошибка — $\sqrt{p(1-p)/n}$: при $p \approx 0.8$ и $n = 200$ это около 2.8 п. п., а правдоподобный диапазон — примерно ±2 стандартные ошибки, то есть ±5–6 п. п. Поэтому «LLM дала 0.82, а TF-IDF — 0.79» ещё не значит «LLM лучше»: такую разницу даёт и случай, тем более что 0.79 посчитано на других 600 отзывах. Честное сравнение — обе модели на **одних и тех же** отзывах, с подсчётом, где верна только одна из них (задача «LLM и TF-IDF на одних отзывах»). Это то же правило, что в уроке «Эмбеддинги: векторы слов и отзывов»: разница меньше разброса — не выигрыш.

{{practice: parse-one, parse-llm, llm-cost, llm-check, llm-same}}

## Своя LLM на компьютере: LM Studio

Облачная модель — не единственный вариант. Небольшую языковую модель можно запустить у себя в программе **LM Studio**: отзывы не уходят во внешний сервис, токены не стоят денег, интернет нужен только чтобы скачать модель. Цена — качество: модель на 3–8 млрд параметров заметно слабее больших облачных и отвечает медленнее (скорость зависит от компьютера). Для разметки по закрытому списку меток её часто хватает — и это проверяется так же, как в задаче «Проверка разметки LLM».

Раздел необязательный: задачи урока и курса от LM Studio не зависят.

**Как подключить (один раз):**

1. Скачайте LM Studio с сайта lmstudio.ai (есть для Windows, macOS и Linux) и установите.
2. На вкладке **Discover** (значок лупы) найдите небольшую instruct-модель на 3–8 млрд параметров, например из семейств Qwen, Gemma или Llama, в сжатом варианте Q4 (файл 2–5 ГБ), и скачайте. Затем вверху окна выберите её в списке моделей — **Load**.
3. Откройте вкладку **Developer** (в русском интерфейсе — «Разработчик»), переключите сервер в состояние **Running** (порт 1234) и в настройках сервера включите **Enable CORS** — без этого браузер не пустит страницу курса к модели. То же из терминала: `lms server start --cors`.
4. Посмотрите на индикатор ниже (и «LM Studio» в шапке страницы): зелёная точка — всё готово. Курс при этом должен быть открыт через запускалку — файл «Курс-Windows.bat», «Курс.command» или «Курс-Linux.sh» из архива курса (см. «КАК ЗАПУСТИТЬ.txt»): он поднимает локальный сервер и открывает сайт по адресу `http://127.0.0.1:8000`. Со страницы, открытой как файл (`file://…`) или с внешнего сайта, браузер к LM Studio не пустит.

::: widget lm-studio
Статус подключения к LM Studio на этом компьютере. Если не подключено — подсказка говорит, какой шаг не сделан.
:::

Когда индикатор зелёный, Python на странице может обращаться к модели. В браузере для этого есть небольшой модуль курса `local_llm`: `models()` — список моделей, `ask(вопрос)` — ответ строкой. Примеры ниже работают только при подключённом LM Studio, в проверке курса они не запускаются.

```python llm
import local_llm

print(local_llm.models())
print(local_llm.ask("Ответь одним словом: какой напиток готовят из эспрессо и молока с пенкой?"))
```

Теперь разметим несколько отзывов той же инструкцией, что и для облачной модели, и сразу проверим каждый ответ:

```python llm
import json
import local_llm

TOPICS = {"кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера"}
PROMPT = """Ты размечаешь отзывы о кофейнях.
Верни ТОЛЬКО JSON вида {"sentiment": ..., "topic": ...}, без пояснений.
sentiment: "positive" или "negative".
topic: одно из "кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера".

Отзыв: """

reviews = [
    "Курьер опоздал на сорок минут, кофе остыл.",
    "Очень вкусный раф, бариста всегда улыбается.",
    "Круассан черствый, как будто вчерашний.",
    "Дороговато для такого района.",
    "Уютно, тихая музыка, можно поработать с ноутбуком.",
]

for text in reviews:
    raw = local_llm.ask(PROMPT + text, max_tokens=60)
    try:
        ans = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])   # вырезаем JSON, даже если модель что-то добавила
    except ValueError:
        ans = None
    ok = isinstance(ans, dict) and ans.get("topic") in TOPICS and ans.get("sentiment") in ("positive", "negative")
    print("✓" if ok else "✗", text[:45], "→", ans if ok else raw[:60])
```

**Что здесь происходит:**

- `local_llm.ask(PROMPT + text, max_tokens=60)` — запрос к модели в LM Studio; `temperature=0` стоит по умолчанию, рассуждения вида `<think>…</think>` (их пишут некоторые модели) модуль вырезает.
- `raw[raw.index("{"): raw.rindex("}") + 1]` — берём кусок от первой `{` до последней `}`: маленькие модели любят добавить «Вот ответ:». Если скобок нет, `index` бросит `ValueError`, и ответ попадёт в «не разобрался».
- `ok` — проверка по закрытому списку: тема из шести и тональность из двух. Ответы с `✗` — та самая кучка «не удалось», которую считают отдельно.

В своём Jupyter то же самое делают клиентом `openai`: LM Studio принимает запросы в формате OpenAI, меняется только адрес.

```python static
# uv add openai
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")   # ключ не проверяется, но параметр обязателен
resp = client.chat.completions.create(
    model="имя-модели-из-LM-Studio",          # как в списке local_llm.models() или на вкладке Developer
    temperature=0, max_tokens=60,
    messages=[{"role": "user", "content": PROMPT + "Курьер опоздал на сорок минут, кофе остыл."}],
)
print(resp.choices[0].message.content)
```

::: warn Типичные ошибки
- **Индикатор жёлтый: «не разрешает запросы со страницы».** Не включён CORS в настройках сервера LM Studio. Включите и нажмите «Проверить снова».
- **«Сервер работает, но модели нет».** Модель скачана, но не загружена: выберите её вверху окна LM Studio (Load).
- **Первый ответ идёт долго.** LM Studio загружает модель в память; следующие ответы быстрее. Если ответы медленные всегда — возьмите модель поменьше.
- **Ответ не разбирается как JSON.** Обычное дело для маленьких моделей: поэтому каждый ответ проверяют кодом, а долю «не разобралось» считают на размеченной выборке.
:::

## Практика

## task: parse-one | Вырезать JSON из ответа | warmup

Модель ответила с лишними словами: `answer` в заготовке. Вырежьте кусок от первой `{` до последней `}` и разберите его `json.loads` в словарь `d`. Сохраните `topic` — значение темы из него.

### starter
```python
import json
answer = 'Конечно! Вот разметка: {"sentiment": "negative", "topic": "доставка"} Надеюсь, помог.'

```

### check
```python
d = need('d', dict)
assert d == {'sentiment': 'negative', 'topic': 'доставка'}, f'd = {d}.'
assert need('topic') == 'доставка', f'topic = {need("topic")!r}.'
```

### hint
Границы куска — `answer.index("{")` и `answer.rindex("}")`; правая граница среза не включается, поэтому к ней прибавляют 1.

### hint
`d = json.loads(answer[answer.index("{"): answer.rindex("}") + 1])`, тема — `d["topic"]`.

### solution
```python
import json
answer = 'Конечно! Вот разметка: {"sentiment": "negative", "topic": "доставка"} Надеюсь, помог.'

d = json.loads(answer[answer.index("{"): answer.rindex("}") + 1])
topic = d["topic"]
print(d, topic)
```

### explain
`json.loads` на всей строке упал бы с `JSONDecodeError`: «Конечно! Вот…» — не JSON. Вырезание от первой `{` до последней `}` спасает от вступлений и подписей — самой частой «болезни» ответов. От оборванного JSON или темы вне списка оно не спасает: это ловит проверка в задаче «Разбор ответов LLM».

## task: parse-llm | Разбор ответов LLM | plus

В `raw` — восемь ответов языковой модели на промпт из урока. Разберите их в DataFrame `parsed` с колонками `sentiment`, `topic`, `ok` (по строке на ответ, в том же порядке). Правила: из ответа берётся текст от первой `{` до последней `}` и разбирается `json.loads`; ответ годен (`ok=True`), только если JSON разобрался, `sentiment` — из `positive`/`negative`, а `topic` — из шести тем. У негодных ответов `sentiment` и `topic` — `None` (в напечатанной таблице pandas покажет их как `NaN` — это нормально: `isna()` находит оба). Сохраните также `n_bad` — число негодных.

### setup
```python
TOPICS = ["кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера"]
raw = [
    '{"sentiment": "negative", "topic": "доставка"}',
    '```json\n{"sentiment": "positive", "topic": "кофе"}\n```',
    'Конечно! Вот разметка: {"sentiment": "positive", "topic": "атмосфера"}',
    '{"sentiment": "negative", "topic": "цена"',
    '{"sentiment": "neutral", "topic": "еда"}',
    '{"sentiment": "negative", "topic": "парковка"}',
    '{"sentiment": "positive", "topic": "обслуживание"}',
    'Не могу определить тему этого отзыва.',
]
```

### starter
```python
import json
import pandas as pd

def parse(answer):
    ...

```

### check
```python
import pandas as _pd
p = need('parsed', _pd.DataFrame)
assert len(p) == 8, f'Строк {len(p)}, а нужно 8.'
assert {'sentiment', 'topic', 'ok'} <= set(p.columns), f'Колонки: {list(p.columns)}.'
okw = [True, True, True, False, False, False, True, False]
assert [bool(x) for x in p['ok']] == okw, f'ok = {list(p["ok"])}, а нужно {okw}.'
assert list(p.loc[[0, 1, 2, 6], 'topic']) == ['доставка', 'кофе', 'атмосфера', 'обслуживание'], 'Темы годных ответов разобраны неверно.'
assert list(p.loc[[0, 1, 2, 6], 'sentiment']) == ['negative', 'positive', 'positive', 'positive'], 'Тональности годных ответов разобраны неверно.'
assert p.loc[[3, 4, 5, 7], ['sentiment', 'topic']].isna().all().all(), 'У негодных ответов sentiment и topic должны быть None.'
assert need('n_bad') == 4, f'n_bad = {need("n_bad")}.'
```

### hint
Начните с функции `parse(answer)`, возвращающей словарь `{"sentiment": ..., "topic": ..., "ok": ...}`; таблица — `pd.DataFrame([parse(a) for a in raw])`.

### hint
`answer.find("{")` и `answer.rfind("}")` дают границы; если одной нет — ответ негоден. `json.loads` оберните в `try/except json.JSONDecodeError`.

### solution
```python
import json
import pandas as pd

def parse(answer):
    bad = {"sentiment": None, "topic": None, "ok": False}
    i, j = answer.find("{"), answer.rfind("}")
    if i == -1 or j < i:
        return bad
    try:
        d = json.loads(answer[i:j + 1])
    except json.JSONDecodeError:
        return bad
    if d.get("sentiment") not in ("positive", "negative") or d.get("topic") not in TOPICS:
        return bad
    return {"sentiment": d["sentiment"], "topic": d["topic"], "ok": True}

parsed = pd.DataFrame([parse(a) for a in raw])
n_bad = int((~parsed["ok"]).sum())
print(parsed)
```

### explain
Половина ответов негодна, и у каждого своя причина: оборванный JSON, метка «neutral» вне списка, выдуманная тема, отказ. Обёртки вида «```json» и «Конечно! Вот…» разбор переживает. В реальной разметке негодных обычно единицы процентов — но их надо считать, а не терять.

## task: llm-cost | Сколько стоит разметить новые отзывы | base

Прикиньте стоимость разметки 4800 новых отзывов `reviews_new.csv` облачной моделью: по одному запросу на отзыв, инструкция `PROMPT` из урока (в заготовке). Для прикидки: входных токенов в запросе — `(len(PROMPT) + len(text)) / 3`, выходных — 20 на ответ; цены условные — 0.3 ₽ за 1000 входных и 1.5 ₽ за 1000 выходных токенов. Сохраните `tokens_in` (целое, округлите сумму), `tokens_out`, `cost` — стоимость в рублях (1 знак) и `share_prompt` — долю входных токенов, которая приходится на инструкцию (3 знака).

### setup
```python
import pandas as pd
new = pd.read_csv("reviews_new.csv")
PROMPT = """Ты размечаешь отзывы о кофейнях.
Верни ТОЛЬКО JSON вида {"sentiment": ..., "topic": ...}, без пояснений.
sentiment: "positive" или "negative".
topic: одно из "кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера".

Отзыв: """
```

### starter
```python
# уже есть: new (4800 отзывов), PROMPT

```

### check
```python
import pandas as _pd
n0 = _pd.read_csv('reviews_new.csv'); P = need('PROMPT')
ti = sum((len(P) + len(t)) / 3 for t in n0['text'])
assert need('tokens_in') == round(ti), f'tokens_in = {need("tokens_in")}, а нужно {round(ti)}: сумма (len(PROMPT) + len(text)) / 3 по всем отзывам.'
assert need('tokens_out') == 20 * len(n0), f'tokens_out = {need("tokens_out")}.'
c = round(ti / 1000 * 0.3 + 20 * len(n0) / 1000 * 1.5, 1)
assert close(need('cost'), c, 0.11), f'cost = {need("cost")}, а нужно {c}. Цены — за 1000 токенов.'
sp = round(len(P) * len(n0) / 3 / ti, 3)
assert close(need('share_prompt'), sp, 0.0015), f'share_prompt = {need("share_prompt")}, а нужно {sp}.'
```

### hint
Входные токены: `sum((len(PROMPT) + len(t)) / 3 for t in new["text"])`, затем `round(...)`. Выходные — `20 * len(new)`.

### hint
`cost = round(tokens_in / 1000 * 0.3 + tokens_out / 1000 * 1.5, 1)`. На инструкцию приходится `len(PROMPT) * len(new) / 3` токенов — поделите на неокруглённую сумму входных.

### solution
```python
total_in = sum((len(PROMPT) + len(t)) / 3 for t in new["text"])
tokens_in = round(total_in)
tokens_out = 20 * len(new)
cost = round(tokens_in / 1000 * 0.3 + tokens_out / 1000 * 1.5, 1)
share_prompt = round(len(PROMPT) * len(new) / 3 / total_in, 3)
print(tokens_in, tokens_out, cost, share_prompt)
```

### explain
Около 456 тысяч входных и 96 тысяч выходных токенов — по условным ценам около 281 ₽. Главное в другом: 81 % входа — одна и та же инструкция, повторённая 4800 раз, потому что отзывы короткие. Если отправлять отзывы пачками (например, по 20 в запросе с просьбой вернуть список JSON), вход сократится в разы, — но тогда разбор ответа сложнее, и проверка на разметке нужна заново. Числа здесь — прикидка: настоящее число токенов и цены берут у провайдера и сверяют со счётом за пробный прогон на сотне отзывов.

## task: llm-check | Проверка разметки LLM | plus

Прежде чем размечать все отзывы языковой моделью, её проверяют на размеченной выборке. В заготовке — `check` (200 отзывов с настоящей темой `topic`) и `llm_topic` — условные ответы модели на них (уже разобранные строки; `None` — ответ не разобрался). Сохраните `n_invalid` — число ответов `None` или не из шести тем, `acc_llm` — долю верных среди **всех** 200 (негодный ответ — ошибка), 3 знака, `recall_by_topic` — Series полноты по темам (3 знака) и `worst` — тему с наименьшей полнотой. Затем оцените погрешность: `low` и `high` — границы `acc_llm ± 2 · √(acc_llm · (1 − acc_llm) / 200)` (3 знака), и `clearly_better` — `True`, только если даже нижняя граница выше 0.79 (точность модели тем из урока «Классификация текстов»).

### setup
```python
import random
import pandas as pd
_r = pd.read_csv("reviews_text.csv")
check = _r.sample(200, random_state=5).reset_index(drop=True)
TOPICS = ["кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера"]
_rnd = random.Random(15)
llm_topic = []
for _t in check["topic"]:
    _u = _rnd.random()
    if _u < 0.04:
        llm_topic.append(None)
    elif _u < 0.06:
        llm_topic.append("сервис")
    elif _u < (0.30 if _t == "атмосфера" else 0.16):
        llm_topic.append(_rnd.choice([x for x in TOPICS if x != _t]))
    else:
        llm_topic.append(_t)
```

### starter
```python
import pandas as pd

ans = pd.Series(llm_topic)
true = check["topic"]

```

### check
```python
import pandas as _pd
c0, L, T = need('check'), _pd.Series(need('llm_topic')), need('TOPICS')
valid = L.isin(T)
assert need('n_invalid') == int((~valid).sum()), f'n_invalid = {need("n_invalid")}.'
ok = (L == c0['topic']) & valid
assert close(need('acc_llm'), round(float(ok.mean()), 3), 0.0011), f'acc_llm = {need("acc_llm")}.'
rec = ok.groupby(c0['topic']).mean().round(3)
g = need('recall_by_topic', _pd.Series)
assert all(close(g[k], rec[k], 0.0011) for k in rec.index), f'recall_by_topic:\n{g}\nа нужно\n{rec}'
assert need('worst') == rec.idxmin(), f'worst = {need("worst")!r}.'
import math as _m
a = float(ok.mean()); se = _m.sqrt(a * (1 - a) / len(c0))
assert close(need('low'), round(a - 2 * se, 3), 0.0015) and close(need('high'), round(a + 2 * se, 3), 0.0015), f'low, high = {need("low")}, {need("high")}, а нужно {round(a - 2 * se, 3)}, {round(a + 2 * se, 3)}.'
assert bool(need('clearly_better')) == bool(a - 2 * se > 0.79), 'clearly_better: сравните с 0.79 нижнюю границу low, а не саму долю.'
```

### hint
Годные ответы — те, что входят в список тем: `ans.isin(TOPICS)`; `None` туда не входит, так что одна маска покрывает оба случая.

### hint
Верный ответ — годный и совпадающий с настоящей темой: `ok = ans.isin(TOPICS) & (ans == true)`. Его среднее — доля верных среди всех.

### hint
Полнота по темам — среднее `ok` в группах настоящей темы: `ok.groupby(true).mean()`. Погрешность — `se = math.sqrt(acc * (1 - acc) / len(true))` по неокруглённой доле.

### solution
```python
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
```

### explain
Условная модель верна в 82.5 % случаев без единого обучающего примера. Но погрешность на 200 отзывах — около 2.7 п. п., и диапазон 0.771–0.879 захватывает 0.79: честный вывод — «не хуже обученной модели», а не «лучше» (`clearly_better = False`). К тому же 0.79 посчитано на других отзывах; на одних и тех же их сравнивает следующая задача. Но 14 ответов из 200 негодны (пустые или «сервис» — темы нет в списке), и они в расчёте честно считаются ошибками. Хуже всего — «атмосфера» (около 2/3), как и у обученной модели: тема размытая. Такой разбор и есть решение «можно ли доверять разметке»: где модель слаба, там нужна ручная проверка. Важно: ответы в задаче условные (сгенерированы для упражнения); на живой модели числа будут свои — и проверять их нужно точно так же.

## task: llm-same | LLM и TF-IDF на одних отзывах | plus

Сравните условную LLM из задачи «Проверка разметки LLM» с моделью тем на **тех же** 200 отзывах. Обучите `make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))` на темах всех остальных 2200 отзывов (без 200 проверочных — иначе модель видела бы ответы) и предскажите темы `check`. Сохраните `acc_model` (3 знака), `llm_only` — сколько отзывов LLM разметила верно, а модель нет, и `model_only` — наоборот.

### setup
```python
import random
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
check = r.sample(200, random_state=5).reset_index(drop=True)
TOPICS = ["кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера"]
_rnd = random.Random(15)
llm_topic = []
for _t in check["topic"]:
    _u = _rnd.random()
    if _u < 0.04:
        llm_topic.append(None)
    elif _u < 0.06:
        llm_topic.append("сервис")
    elif _u < (0.30 if _t == "атмосфера" else 0.16):
        llm_topic.append(_rnd.choice([x for x in TOPICS if x != _t]))
    else:
        llm_topic.append(_t)
ok_llm = pd.Series(llm_topic).isin(TOPICS) & (pd.Series(llm_topic) == check["topic"])
```

### starter
```python
# уже есть: r, check, ok_llm — верна ли LLM на каждом из 200 отзывов

```

### check
```python
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _T
from sklearn.linear_model import LogisticRegression as _LR
r0, c0, ol = need('r'), need('check'), need('ok_llm')
rest = r0[~r0['review_id'].isin(c0['review_id'])]
okm = _mp(_T(), _LR(max_iter=1000)).fit(rest['text'], rest['topic']).predict(c0['text']) == c0['topic'].values
am = round(float(okm.mean()), 3)
assert close(need('acc_model'), am, 0.004), f'acc_model = {need("acc_model")}, а нужно около {am}. Обучайте на 2200 отзывах без проверочных (по review_id).'
lo, mo = int((ol.values & ~okm).sum()), int((okm & ~ol.values).sum())
assert abs(need('llm_only') - lo) <= 1 and abs(need('model_only') - mo) <= 1, f'llm_only, model_only = {need("llm_only")}, {need("model_only")}, а нужно около {lo}, {mo}.'
```

### hint
Обучающая часть — отзывы, которых нет среди проверочных: `rest = r[~r["review_id"].isin(check["review_id"])]`.

### hint
Верность модели — `ok_model = pd.Series(model.predict(check["text"])) == check["topic"]`; «только LLM» — `(ok_llm & ~ok_model).sum()`.

### solution
```python
rest = r[~r["review_id"].isin(check["review_id"])]
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(rest["text"], rest["topic"])
ok_model = pd.Series(model.predict(check["text"])) == check["topic"]
acc_model = round(float(ok_model.mean()), 3)
llm_only = int((ok_llm & ~ok_model).sum())
model_only = int((ok_model & ~ok_llm).sum())
print(acc_model, llm_only, model_only)
```

### explain
На этих 200 отзывах модель тем верна в 75.5 % случаев — ниже своих 79 % на тесте из урока «Классификация текстов»: на 200 отзывах доля колеблется на несколько пунктов. LLM здесь впереди на 7 п. п., но разницу решают только отзывы, где модели разошлись: 38 в пользу LLM против 24 в пользу TF-IDF, на остальных обе правы или обе ошиблись. 38 против 24 — перевес, но на 62 спорных отзывах он ещё может оказаться случайным; для уверенного вывода нужна выборка побольше. Главный урок: сравнивать модели надо на одних и тех же отзывах и смотреть на расхождения, а не на две доли с разных выборок.
