---
title: "Разметка текстов языковой моделью"
lead: "Большая языковая модель размечает отзывы по описанию, без обучающих примеров. Разбираем, как написать инструкцию с закрытым списком меток, превратить ответ-строку в данные и проверить разметку на выборке с известными ответами, — и как запустить небольшую модель у себя на компьютере в LM Studio."
files: [reviews_text.csv, reviews_new.csv]
recap:
  - "LLM размечает тексты по инструкции без обучения (zero-shot). Ответ — строго JSON из фиксированных меток, и его обязательно проверяют на размеченной выборке."
  - "Небольшую LLM можно запустить у себя в LM Studio: отзывы не уходят во внешний сервис, но модель слабее облачной — её проверяют на размеченной выборке так же."
  - "Доля верных на 200 отзывах имеет погрешность около ±5 п. п. (±2 · √(p(1 − p)/n)); сравнивать LLM с обученной моделью нужно на одних и тех же отзывах, по числу случаев, где права только одна."
---

Все карточки, включая сравнение на общих 200 отзывах, выполняются в браузере на подготовленных ответах. Примеры SDK и LM Studio — отдельный эксперимент.

Разметку языковой моделью проверяют так же, как разметку людьми в уроке «Качество разметки: голосование, каппа, золотой набор»: на выборке с известными ответами, с матрицей ошибок.

## Разметка большой языковой моделью

Большая языковая модель (LLM) умеет выполнить задачу по описанию, без обучающих примеров — это называют **zero-shot**. Для аналитика это значит: можно разметить тысячу отзывов по темам, которых не было в исходных данных, за минуты. Но ответ модели — текст, и его нужно превратить в данные.

```python static
# uv add anthropic   (или клиент вашего провайдера — схема та же)
import json
import anthropic

client = anthropic.Anthropic()          # ключ берётся из переменной окружения ANTHROPIC_API_KEY
MODEL = "..."                           # имя модели из документации провайдера; запишите его и дату проверки

PROMPT = """Ты размечаешь отзывы о кофейнях.
Верни ТОЛЬКО JSON вида {"sentiment": ..., "topic": ...}, без пояснений.
sentiment: "positive" или "negative".
topic: одно из "кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера".

Отзыв: """

def label(text):
    msg = client.messages.create(
        model=MODEL, max_tokens=50,
        messages=[{"role": "user", "content": PROMPT + text}],
    )
    if msg.stop_reason != "end_turn":     # обрезан по max_tokens, отказ и т. п. — в кучку «не удалось»
        return None
    return next((b.text for b in msg.content if b.type == "text" and isinstance(b.text, str) and b.text.strip()), None)

answer = label("Курьер опоздал на сорок минут, кофе остыл.")
print(answer if answer is not None else "Нет завершённого текста. Отметьте этот отзыв как неразобранный.")
```

**Что здесь происходит:**

- `anthropic.Anthropic()` — клиент API; ключ берётся из переменной окружения, в коде его не пишут.
- `PROMPT` — инструкция: что сделать, в каком формате ответить и какие метки допустимы. Текст отзыва дописывается в конец.
- `messages.create(...)` — один запрос к модели; `max_tokens=50` — ответ короткий (нам нужен только JSON). Других параметров не передаём: например, `temperature` новые модели Claude менять не разрешают — запрос с `temperature=0` получит ошибку 400. Какие параметры принимает выбранная модель, смотрят в документации провайдера.
- `msg.stop_reason` — почему модель остановилась. `"end_turn"` — закончила ответ; `"max_tokens"` — ответ обрезан, такой JSON не разберётся. Такие случаи не выбрасывают, а считают отдельно.
- `msg.content` — список блоков ответа; берём первый текстовый (у части моделей перед ним бывают другие блоки, поэтому не `content[0]`). Это **строка**: в ней может оказаться не только JSON, поэтому её ещё нужно разобрать и проверить (задача «Разбор ответов LLM»).

::: figure llm-label-flow
Разметка LLM как конвейер: инструкция с закрытым списком меток → ответ-строка → разбор JSON → проверка меток. Ответы, не прошедшие разбор или проверку, — отдельная кучка, а качество меряют на выборке с известными метками до разметки всего.
:::

Правила, без которых разметка LLM превращается в лотерею:

1. **Закрытый список меток.** Перечислите допустимые значения прямо в инструкции и проверяйте каждый ответ: модель может придумать «парковку» или «нейтрально».
2. **Машиночитаемый формат.** Просите JSON и разбирайте его кодом; всё, что не разобралось, — отдельная кучка «не удалось», а не молча выброшенные строки.
3. **Повторяемость не обещана.** Один и тот же отзыв может получить разные ответы — даже там, где `temperature` можно поставить в 0, провайдеры не гарантируют одинаковых ответов, а у новых моделей Claude этот параметр вообще не настраивается. Поэтому качество меряют не совпадением ответов, а долей верных на выборке с известными метками, а в отчёте записывают имя модели и дату прогона.
4. **Проверка на разметке.** Прежде чем размечать всё, прогоните 100–200 текстов с известными метками и посчитайте точность и матрицу ошибок — ровно как для любой модели в этом курсе.
5. **Стоимость и данные.** Оплата — за токены (куски слов), отдельно за входные (инструкция + отзыв) и выходные (ответ): прикиньте объём заранее. Точное число токенов знает только токенизатор провайдера; для прикидки по русскому тексту можно брать около одного токена на три символа и потом сверить со счётом за пробный прогон. И не отправляйте внешнему сервису персональные данные клиентов без разрешения.

Если вызов SDK завершился исключением, сохраните ID отзыва и статус «ошибка запроса». Если ответ пришёл, проверьте причину остановки, наличие текста и затем значения полей. Так различаются ошибка вызова, незавершённый ответ и неверная метка. В журнале остаётся каждый исходный ID. Во внешний сервис отправляют только разрешённый к передаче текст, а связь ответа с `review_id` сохраняют у себя.

**Схема ответа вместо просьбы.** Многие API умеют сами ограничивать ответ заданной JSON-схемой — это называют structured outputs. У Claude это параметр `output_config`, у LM Studio и OpenAI-совместимых серверов — `response_format`. Закрытый список меток тогда задаётся в схеме через `enum`:

```python static
SCHEMA = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string", "enum": ["positive", "negative"]},
        "topic": {"type": "string", "enum": ["кофе", "еда", "обслуживание", "доставка", "цена", "атмосфера"]},
    },
    "required": ["sentiment", "topic"],
    "additionalProperties": False,
}

msg = client.messages.create(
    model=MODEL, max_tokens=50,
    messages=[{"role": "user", "content": "Определи тональность и тему отзыва о кофейне.\n\n Отзыв: " + text}],
    output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
)
```

Схема поддерживается не всеми моделями — список есть в документации провайдера. И она снимает только часть проблем: ответ будет разбираться и метки будут из списка, но **правильность** темы схема не проверяет, а обрезанный по `max_tokens` ответ или отказ отвечать по-прежнему возможны. Поэтому разбор с кучкой «не удалось» и проверка на выборке с известными метками остаются — схема просто делает кучку меньше. Регистр меток модель может изменить, так что сравнивать их надёжнее после `.lower()`.

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

**Как сравнивать LLM с обученной моделью.** Проверка на 200 отзывах даёт долю верных с погрешностью. Для доли $p$ на $n$ отзывах стандартная ошибка — $\sqrt{p(1-p)/n}$: при $p \approx 0.8$ и $n = 200$ это около 2.8 п. п., а правдоподобный диапазон — примерно ±2 стандартные ошибки, то есть ±5–6 п. п. Поэтому «LLM дала 0.82, а TF-IDF — 0.79» ещё не значит «LLM лучше»: такую разницу даёт и случай, тем более что 0.79 посчитано на других 600 отзывах. Честное сравнение — обе модели на **одних и тех же** отзывах, с подсчётом, где верна только одна из них (задача «LLM и TF-IDF на одних отзывах»). Отдельные интервалы для двух долей не дают парный интервал разницы.

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
    ok = (isinstance(ans, dict) and isinstance(ans.get("topic"), str)
          and ans["topic"] in TOPICS and ans.get("sentiment") in ("positive", "negative"))
    print("✓" if ok else "✗", text[:45], "→", ans if ok else raw[:60])
```

**Что здесь происходит:**

- `local_llm.ask(PROMPT + text, max_tokens=60)` — запрос к модели в LM Studio; `temperature=0` стоит по умолчанию, рассуждения вида `<think>…</think>` (их пишут некоторые модели) модуль вырезает.
- `raw[raw.index("{"): raw.rindex("}") + 1]` — берём кусок от первой `{` до последней `}`: маленькие модели любят добавить «Вот ответ:». Если скобок нет, `index` бросит `ValueError`, и ответ попадёт в «не разобрался».
- `ok` — проверка по закрытому списку: тема из шести и тональность из двух. При пустом списке вариантов, усечённой генерации или отсутствии текста `ask` возвращает пустую строку. В этой строке сохраняем `✗` и переходим к следующему отзыву.

В своём Jupyter то же самое делают клиентом `openai`: LM Studio принимает запросы в формате OpenAI, меняется только адрес.

```python static
# uv add openai
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")   # для локального сервера без аутентификации; при включённой защите нужен его токен
resp = client.chat.completions.create(
    model="имя-модели-из-LM-Studio",          # как в списке local_llm.models() или на вкладке Developer
    temperature=0, max_tokens=60,
    messages=[{"role": "user", "content": PROMPT + "Курьер опоздал на сорок минут, кофе остыл."}],
)
choice = resp.choices[0] if resp.choices else None
answer = choice.message.content if choice and choice.finish_reason == "stop" else None
if isinstance(answer, str) and answer.strip():
    print(answer)                         # дальше проверяем JSON и обе метки
else:
    print("Нет завершённого текста. Отметьте этот отзыв как неразобранный.")
```

::: warn Типичные ошибки
- **Индикатор жёлтый: «не разрешает запросы со страницы».** Не включён CORS в настройках сервера LM Studio. Включите и нажмите «Проверить снова».
- **«Сервер работает, но модели нет».** Модель скачана, но не загружена: выберите её вверху окна LM Studio (Load).
- **Первый ответ идёт долго.** LM Studio загружает модель в память; следующие ответы быстрее. Если ответы медленные всегда — возьмите модель поменьше.
- **Ответ не разбирается как JSON.** Обычное дело для маленьких моделей: поэтому каждый ответ проверяют кодом, а долю «не разобралось» считают на размеченной выборке.
:::

Метки и ответы LLM в упражнениях синтетические; цены — условные входы задачи, а не актуальный тариф. Учебный результат воспроизводится по заготовленным ответам без платных вызовов. Пустой успешный ответ трактуйте как отказ/ошибку разбора, а не допустимую метку. Сравнивайте методы на одних текстах с эталонной разметкой, покажите парные расхождения и отказы; допустимый проигрыш задайте до просмотра результата.

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

В `raw` — восемь ответов языковой модели на промпт из урока. Разберите их в DataFrame `parsed` с колонками `sentiment`, `topic`, `ok` (по строке на ответ, в том же порядке). Правила: из ответа берётся текст от первой `{` до последней `}` и разбирается `json.loads`; ответ годен (`ok=True`), только если JSON разобрался, `sentiment` — из `positive`/`negative`, а `topic` — из шести тем. У негодных ответов `sentiment` и `topic` — `None` (в напечатанной таблице pandas покажет их как `NaN` — это нормально: `isna()` находит оба). Ваша функция `parse(answer)` должна обработать и новый отзыв. Для одного ответа верните три поля `sentiment`, `topic`, `ok` как словарь либо как значения в этом порядке. Пустая строка или отсутствие текста (`None` из облачного примера) считаются негодным ответом. Сохраните также `n_bad` — число негодных.

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
p = p.reset_index(drop=True)
assert len(p) == 8, f'Строк {len(p)}, а нужно 8.'
assert {'sentiment', 'topic', 'ok'} <= set(p.columns), f'Колонки: {list(p.columns)}.'
okw = [True, True, True, False, False, False, True, False]
assert [bool(x) for x in p['ok']] == okw, f'ok = {list(p["ok"])}, а нужно {okw}.'
assert list(p.loc[[0, 1, 2, 6], 'topic']) == ['доставка', 'кофе', 'атмосфера', 'обслуживание'], 'Темы годных ответов разобраны неверно.'
assert list(p.loc[[0, 1, 2, 6], 'sentiment']) == ['negative', 'positive', 'positive', 'positive'], 'Тональности годных ответов разобраны неверно.'
assert p.loc[[3, 4, 5, 7], ['sentiment', 'topic']].isna().all().all(), 'У негодных ответов sentiment и topic должны быть None.'
_parse = need('parse')
import json as _json
_cases = [(None, (None, None, False)), ('', (None, None, False)), ('{"topic":["еда"],"sentiment":"positive"}', (None, None, False)), ('{"sentiment":"positive","topic":"парковка"}', (None, None, False)), ('{"sentiment":"neutral","topic":"кофе"}', (None, None, False))]
for _topic in ['кофе', 'еда', 'обслуживание', 'доставка', 'цена', 'атмосфера']:
    for _sentiment in ['positive', 'negative']:
        _cases.append((_json.dumps(dict(topic=_topic, sentiment=_sentiment), ensure_ascii=False), (_sentiment, _topic, True)))
for _answer, _expected in _cases:
    try:
        _row = _parse(_answer)
    except (AttributeError, TypeError):
        if _answer is None:
            raise AssertionError('None здесь означает отсутствие текста от SDK. Верните негодную запись: sentiment=None, topic=None, ok=False; допустима и последовательность этих трёх значений.')
        raise
    _fields = ['sentiment', 'topic', 'ok']
    if isinstance(_row, (dict, _pd.Series)):
        assert all(_key in _row for _key in _fields), 'Укажите sentiment, topic и ok в возвращаемой записи.'
        _row = tuple(_row[_key] for _key in _fields)
    assert isinstance(_row, (tuple, list)) and tuple(_row) == _expected, f'parse({_answer!r}): ожидалось {_expected}. Проверьте разрешённые темы, тональности и негодный ответ.'
assert need('n_bad') == 4, f'n_bad = {need("n_bad")}.'
```

### hint
Начните с функции `parse(answer)`, возвращающей словарь `{"sentiment": ..., "topic": ..., "ok": ...}`; таблица — `pd.DataFrame([parse(a) for a in raw])`.

### hint
Если `answer` не строка (например, `None`), сразу верните негодную запись. Для строки `answer.find("{")` и `answer.rfind("}")` дают границы; если одной нет — ответ негоден. `json.loads` оберните в `try/except json.JSONDecodeError`.

### solution
```python
import json
import pandas as pd

def parse(answer):
    bad = {"sentiment": None, "topic": None, "ok": False}
    if not isinstance(answer, str):
        return bad
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
Половина ответов негодна, и у каждого своя причина: оборванный JSON, метка «neutral» вне списка, выдуманная тема, отказ. Обёртки вида «```json» и «Конечно! Вот…» разбор переживает. Величину доли отказов узнают по собственному прогону. Сохраняйте по строке на каждый отправленный отзыв.

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

Прежде чем размечать все отзывы языковой моделью, её проверяют на размеченной выборке. В заготовке — `check` (200 отзывов с настоящей темой `topic`) и `llm_topic` — условные ответы модели на них (уже разобранные строки; `None` — ответ не разобрался). Сохраните `n_invalid` — число ответов `None` или не из шести тем, `acc_llm` — долю верных среди **всех** 200 (негодный ответ — ошибка), 3 знака, `recall_by_topic` — Series полноты по темам (3 знака) и `worst` — тему с наименьшей полнотой. Затем оцените погрешность: `low` и `high` — границы `acc_llm ± 2 · √(acc_llm · (1 − acc_llm) / 200)` (3 знака), и `above_reference` — `True`, только если неокруглённая нижняя граница интервала этой одной доли правильных выше фиксированного числа 0.79. Это сравнение с числом, а не доказательство разницы между моделями: парная проверка двух систем на одних отзывах будет в следующей задаче.

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
# above_reference: нижняя граница одного интервала выше фиксированного числа 0.79

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
assert bool(need('above_reference')) == bool(a - 2 * se > 0.79), 'above_reference: сравните неокруглённую нижнюю границу с фиксированным числом0.79; это не парная разница моделей.'
```

### hint
Годные ответы — те, что входят в список тем: `ans.isin(TOPICS)`; `None` туда не входит, так что одна маска покрывает оба случая.

### hint
Верный ответ — годный и совпадающий с настоящей темой: `ok = ans.isin(TOPICS) & (ans == true)`. Его среднее — доля верных среди всех.

### hint
Полнота по темам — среднее `ok` в группах настоящей темы: `ok.groupby(true).mean()`. Погрешность — `se = math.sqrt(acc * (1 - acc) / len(true))` по неокруглённой доле. Для `above_reference` сравните `acc - 2 * se` с 0.79. Такое сравнение не оценивает разницу двух моделей.

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
above_reference = bool(acc - 2 * se > 0.79)
print(n_invalid, acc_llm, worst, low, high, above_reference)
print(recall_by_topic)
```

### explain
В этом синтетическом опыте верны 82,5 % ответов. Фиксированное число 0,79 попадает в приближённый интервал 0,771–0,879, поэтому `above_reference` равно `False`. Даже значение `True` означало бы только, что нижняя граница интервала одной доли выше этого числа. Разницу качества двух моделей оценивают по парным ответам на одни и те же отзывы; такая проверка будет дальше.

## task: llm-same | LLM и TF-IDF на одних отзывах | plus

Сравните условную LLM из задачи «Проверка разметки LLM» с моделью тем на **тех же** 200 отзывах. Обучите `make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))` на темах всех остальных 2200 отзывов (без 200 проверочных — иначе модель видела бы ответы) и предскажите темы `check`. Сохраните `acc_model` (3 знака), `llm_only` — сколько отзывов LLM разметила верно, а модель нет, и `model_only` — наоборот.

Допустимый проигрыш задан до оценки и равен 2 п.п. Для каждого из 200 отзывов вычтите индикатор правильности TF-IDF из индикатора правильности LLM. В `paired_lower` запишите приближённую нижнюю границу двустороннего 95 %-го интервала для **средней парной разницы** (среднее минус 1,96 выборочной стандартной ошибки, 3 знака). В `within_margin` укажите, выше ли неокруглённая граница −0,02. Неразобранный ответ LLM засчитывается как ошибка.

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
import pandas as _pd
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _T
from sklearn.linear_model import LogisticRegression as _LR
r0, c0, ol = need('r'), need('check'), need('ok_llm')
_original = _pd.read_csv('reviews_text.csv')
_original_check = _original.sample(200,random_state=5).reset_index(drop=True)
assert c0.review_id.is_unique and set(c0.review_id)==set(_original_check.review_id), 'Сравнивайте обе модели на тех же 200 review_id.'
_truth = _original_check.set_index('review_id')
for _key in ['text','topic']:
    assert c0[_key].tolist()==_truth.loc[c0.review_id,_key].tolist(), f'{_key}: сохраните принадлежность исходному review_id.'
_llm_topics = _pd.Series(need('llm_topic'),index=_original_check.review_id)
_expected_ol = c0.review_id.map(_llm_topics).isin(['кофе','еда','обслуживание','доставка','цена','атмосфера']) & c0.review_id.map(_llm_topics).eq(c0.topic)
if isinstance(ol,_pd.Series):
    assert ol.index.is_unique and set(ol.index)==set(c0.index), 'Индикаторы ok_llm должны соответствовать строкам check.'
    ol=ol.reindex(c0.index)
assert list(ol)==list(_expected_ol), 'Не переставляйте отдельно ответы LLM: обе системы сравниваются по одним review_id.'
rest = r0[~r0['review_id'].isin(c0['review_id'])]
okm = _mp(_T(), _LR(max_iter=1000)).fit(rest['text'], rest['topic']).predict(c0['text']) == c0['topic'].values
am = round(float(okm.mean()), 3)
assert close(need('acc_model'), am, 0.004), f'acc_model = {need("acc_model")}, а нужно около {am}. Обучайте на 2200 отзывах без проверочных (по review_id).'
lo, mo = int((ol.values & ~okm).sum()), int((okm & ~ol.values).sum())
assert need('llm_only') == lo and need('model_only') == mo, f'llm_only, model_only = {need("llm_only")}, {need("model_only")}, а нужно около {lo}, {mo}.'
_only_a, _only_b = need('llm_only'), need('model_only')
_n = len(check)
_diff = (_only_a - _only_b) / _n
_se = ((_only_a + _only_b - _n * _diff ** 2) / (_n * (_n - 1))) ** .5
_lower = _diff - 1.96 * _se
assert close(need('paired_lower'),round(_lower,3),.00051), 'Числитель парной разницы определяется расхождениями обеих моделей на тех же ID.'
assert need('within_margin') == (_lower > -.02), 'Сравните неокруглённую нижнюю границу с −0,02.'
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
paired = ok_llm.astype(int) - ok_model.astype(int)
lower = paired.mean() - 1.96 * paired.sem()
paired_lower = round(float(lower), 3)
within_margin = bool(lower > -.02)
print(acc_model, llm_only, model_only)
```

### explain
На общих 200 отзывах верны 165 условных ответов LLM и 151 ответ TF-IDF. Только LLM права 38 раз, только TF-IDF — 24. Разница (38 − 24) / 200 = +7 п. п. Приближённый парный интервал от −0,675 до +14,675 п. п. включает ноль, поэтому превосходство не установлено. Его нижняя граница выше заранее заданных −2 п. п.: в этом учебном сравнении допуск выполнен. В знаменателе остались все отказы.
