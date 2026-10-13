---
title: "Часовые пояса и unix-время"
lead: "Сервер приложения хранит время не датой, а числом секунд с 1970 года и всегда по UTC. Превращаем такие числа в даты, переводим в местное время каждой кофейни — и только потом считаем часы пик."
files: [app_events.csv]
recap:
  - "Unix-время: `pd.to_datetime(ts, unit=\"s\")` (10 цифр) или `unit=\"ms\"` (13 цифр). Это всегда UTC."
  - "Пояса: `dt.tz_localize(\"UTC\")` — приписать, `dt.tz_convert(\"+05:00\")` или `\"Asia/Yekaterinburg\"` — перевести. Несколько городов в одном столбце — сдвиг `utc + pd.to_timedelta(часы, unit=\"h\")`."
---

## Часовые пояса и unix-время

Мобильное приложение «Зерна» пишет события на сервер. Сервер стоит в одном месте, а кофейни — в Перми, Тюмени, Уфе (UTC+5) и Казани (UTC+3, московское время). Поэтому сервер хранит время в **UTC** — всемирном времени без поясов — и не датой, а **unix-временем**: числом секунд (или миллисекунд), прошедших с полуночи 1 января 1970 года по UTC. Аналитику достаётся столбец вида `1791167205892`, и прежде чем считать часы пик, его надо превратить в дату и перевести в местное время.

::: tip Аналогия
Unix-время — как номер кадра в общем видеопотоке, который снимают все камеры мира одновременно: один номер — один момент для всех. Часовой пояс — подпись под кадром «а в Перми на часах было вот столько». Момент один, подписи разные.
:::

### Unix-время → дата

**Пример руками.** В сутках 86 400 секунд. Число `86400` — ровно сутки после начала отсчёта: `1970-01-02 00:00`. Число `1791100800`: делим на 86 400 — получается 20 730 полных суток и остаток 28 800 секунд, то есть 8 часов. 20 730 суток после 1 января 1970 года — 4 октября 2026, значит, момент — `2026-10-04 08:00` по UTC. Руками так никто не считает — для этого есть `unit`:

```python
import pandas as pd
print(pd.to_datetime(0, unit="s"))                 # начало отсчёта
print(pd.to_datetime(86400, unit="s"))             # +1 сутки
print(pd.to_datetime(1791100800, unit="s"))        # секунды
print(pd.to_datetime(1791100800000, unit="ms"))    # то же в миллисекундах
```

Что здесь происходит:

- `unit="s"` — число означает секунды, `unit="ms"` — миллисекунды. Один и тот же момент в миллисекундах — на три нуля длиннее.
- Результат — время **UTC без пояса** («наивное»): pandas не знает, где его показывать.

Как отличить секунды от миллисекунд: у современных дат unix-время в секундах — 10 цифр (`1791100800`), в миллисекундах — 13 (`1791167205892`).

### UTC → местное время

У даты может быть **пояс**. `tz_localize("UTC")` говорит pandas «это время по UTC» (ничего не сдвигая), `tz_convert(...)` переводит в другой пояс — меняет часы, но не момент:

```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
ev["utc"] = pd.to_datetime(ev["ts"], unit="ms")

perm = ev[ev["shop_id"].str.startswith("PRM")].copy()
perm["local"] = perm["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")
print(perm[["utc", "local"]].head(2))
print("пик по UTC:", perm["utc"].dt.hour.value_counts().idxmax(), "ч")
print("пик по Перми:", perm["local"].dt.hour.value_counts().idxmax(), "ч")
```

Что здесь происходит:

- `pd.to_datetime(ev["ts"], unit="ms")` — весь столбец миллисекунд → даты UTC.
- `.dt.tz_localize("UTC")` — приписать пояс. Время на часах не меняется: `02:26` становится `02:26+00:00`.
- `.dt.tz_convert("+05:00")` — перевести в UTC+5: `02:26+00:00` → `07:26+05:00`. Момент тот же, на пермских часах — 07:26.

::: figure tz-shift
Первое пермское событие из `app_events.csv`: один момент на трёх циферблатах. Внизу — чем перевод пояса отличается от переписанной подписи.
:::

Как читать: по UTC «пик» — 8 утра, а по пермским часам это 13:00 — обеденный. Без перевода аналитик отправил бы второго бариста не на ту смену.

::: note Имена поясов: «+05:00» и «Asia/Yekaterinburg»
В рабочем коде пояс пишут по имени из базы поясов: Пермь, Тюмень, Уфа — `"Asia/Yekaterinburg"`, Казань — `"Europe/Moscow"`. В браузерной версии курса этой базы нет, поэтому в примерах — постоянное смещение `"+05:00"` и `"+03:00"`. Для наших городов это одно и то же: летнее время в России отменили в 2011 году, а с октября 2014-го смещение Перми, Тюмени, Уфы и Казани не менялось. Для Европы или США смещение меняется дважды в год — там нужны только имена, иначе половину года время будет сдвинуто на час.

```python static
ev["local"] = ev["utc"].dt.tz_localize("UTC").dt.tz_convert("Asia/Yekaterinburg")
```
:::

### Несколько городов в одном столбце

У столбца pandas может быть только **один** пояс. Если в таблице и Пермь, и Казань, местное время считают сдвигом: у каждой строки своё смещение в часах, а дата остаётся «наивной».

```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
ev["utc"] = pd.to_datetime(ev["ts"], unit="ms")

offset = {"PRM": 5, "TMN": 5, "UFA": 5, "KZN": 3}          # смещение от UTC, часы
hours = ev["shop_id"].str[:3].map(offset)                 # у каждой строки своё
ev["local"] = ev["utc"] + pd.to_timedelta(hours, unit="h")
print("доля событий с 0 до 6 утра по UTC:", round((ev["utc"].dt.hour < 6).mean() * 100, 1), "%")
print("то же по местному времени:", round((ev["local"].dt.hour < 6).mean() * 100, 1), "%")
```

Что здесь происходит:

- `ev["shop_id"].str[:3]` — код города из кода кофейни, `map(offset)` — смещение для каждой строки.
- `pd.to_timedelta(hours, unit="h")` — числа превращаются в интервалы «5 часов», «3 часа»; их прибавляют к времени UTC.
- По UTC четверть событий (26 %) — «ночью», с 0 до 6. По местному времени ночью нет ни одного события: самые ранние приходятся на 7 утра — гости заказывают кофе заранее, к открытию в 8. «Ночь» была утренним пиком, записанным в UTC.

::: warn Типичные ошибки
- **Не та единица.** Миллисекунды, прочитанные как секунды (`unit="s"`), дают даты в далёком будущем — `pd.to_datetime(1791167205892, unit="s")` выдаёт 58729 год. Секунды без `unit` pandas читает как наносекунды — получается `1970-01-01 00:00:01.79…`. Считайте цифры: 10 — секунды, 13 — миллисекунды.
- **`tz_convert` у «наивной» даты.** `TypeError: Cannot convert tz-naive timestamps, use tz_localize to localize` — сначала скажите, в каком поясе время записано (`tz_localize("UTC")`), потом переводите.
- **`tz_localize` вместо `tz_convert`.** `tz_localize("+05:00")` у времени UTC не сдвинет часы, а просто «перепишет подпись» — и момент станет другим на 5 часов.
- **Даты по UTC в отчёте по дням.** Заказ в 01:30 по Перми — это 20:30 предыдущего дня по UTC. Дневные итоги считайте по местному времени.
:::

::: quiz
Те же события пермских кофеен из `app_events.csv`: столбец `ts` — числа вида `1791167205892`. Аналитик сделал `pd.to_datetime(df["ts"], unit="ms")`, посчитал час пик — 8 утра — и поставил второго бариста на утреннюю смену. Что не так?

- [x] Это время UTC; по Перми к нему нужно прибавить 5 часов — пик на самом деле в 13:00, в обед
  > Unix-время всегда отсчитывается в UTC. Перевод в местное время — `tz_localize("UTC")` и `tz_convert("+05:00")` или сдвиг на смещение города. Именно этот пример разобран выше: 8 по UTC — 13 по пермским часам.
- [ ] Нужно было `unit="s"`
  > У числа 13 цифр — это миллисекунды. С `unit="s"` получился бы 58729 год.
- [ ] Всё верно: утро — главное время кофе
  > В зале утренний пик действительно есть, но здесь время записано по UTC. Правдоподобный ответ — самый опасный: ошибку в 5 часов никто не заметит.
- [ ] Надо округлить время через `dt.round("h")`
  > Округление не меняет пояс: 8 утра по UTC останутся 8 утра.
:::

{{practice: unix, local-time}}

## Практика

## task: unix | Время приложения — по Перми | base

В `app_events.csv` время события `ts` — unix-время в миллисекундах (UTC). Для пермских кофеен (`shop_id` начинается с `"PRM"`):

1. превратите `ts` в дату — столбец `utc`;
2. переведите в пермское время (UTC+5) через пояса — столбец `local`;
3. сохраните в `perm_peak` час (число 0–23) по местному времени, на который приходится больше всего событий.

Результат — таблица `perm`.

### starter
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")

```

### check
```python
import pandas as _pd
pm = need('perm', _pd.DataFrame)
assert pm['shop_id'].str.startswith('PRM').all() and len(pm) == 540, f'В perm {len(pm)} строк. Нужны только события пермских кофеен — их 540.'
assert 'utc' in pm.columns and _pd.api.types.is_datetime64_any_dtype(pm['utc']), 'В perm нужен столбец utc — дата из ts.'
assert pm['utc'].min().year == 2026, f'Первая дата в utc — {pm["utc"].min()}. Проверьте единицу: 13 цифр — миллисекунды, unit="ms".'
assert 'local' in pm.columns, 'В perm нужен столбец local — пермское время.'
assert getattr(pm['local'].dt, 'tz', None) is not None, 'У local нет пояса. Сначала tz_localize("UTC"), потом tz_convert("+05:00").'
assert int(pm['local'].iloc[0].hour) == (int(pm['utc'].iloc[0].hour) + 5) % 24, 'Местное время должно быть на 5 часов больше UTC. Не перепутали tz_localize и tz_convert?'
_e = _pd.read_csv('app_events.csv')
_p = _e[_e['shop_id'].str.startswith('PRM')]
_h = (_pd.to_datetime(_p['ts'], unit='ms') + _pd.Timedelta(hours=5)).dt.hour.value_counts().idxmax()
_u = _pd.to_datetime(_p['ts'], unit='ms').dt.hour.value_counts().idxmax()
assert need('perm_peak') != _u or _u == _h, f'perm_peak = {need("perm_peak")} — это час пик по UTC. Возьмите час из столбца local.'
assert int(need('perm_peak')) == int(_h), f'perm_peak = {need("perm_peak")}, а нужно {_h}.'
```

### hint
Три шага: `pd.to_datetime(..., unit="ms")` → `.dt.tz_localize("UTC")` → `.dt.tz_convert("+05:00")`. Не забудьте сначала отобрать пермские кофейни (и сделать `.copy()`, чтобы спокойно добавлять столбцы).

### hint
Час — `perm["local"].dt.hour`; самый частый — `value_counts().idxmax()`.

### hint
```python
perm = ev[ev["shop_id"].str.startswith(...)].copy()
perm["utc"] = pd.to_datetime(perm["ts"], unit=...)
perm["local"] = perm["utc"].dt.tz_localize(...).dt.tz_convert(...)
perm_peak = int(perm["local"].dt.hour.value_counts().idxmax())
```

### solution
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
perm = ev[ev["shop_id"].str.startswith("PRM")].copy()
perm["utc"] = pd.to_datetime(perm["ts"], unit="ms")
perm["local"] = perm["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")
perm_peak = int(perm["local"].dt.hour.value_counts().idxmax())
```

### explain
По пермским часам пик приложения — 13:00, обед. По UTC пик пришёлся бы на 8 утра — ровно на 5 часов раньше, и выглядел бы правдоподобно, поэтому такую ошибку легко не заметить. Если перепутать `tz_localize` и `tz_convert` и написать `tz_localize("+05:00")`, часы останутся прежними, а у них появится неверная подпись «+05:00» — момент сдвинется на 5 часов в другую сторону.

## task: local-time | Утренние заказы по местному времени | plus

В `app_events.csv` события всех городов. Пермь, Тюмень и Уфа живут по UTC+5, Казань — по UTC+3. Переведите время `ts` (unix, миллисекунды, UTC) в местное время каждой кофейни — столбец `local` в таблице `ev` — и посчитайте `morning_share`: долю **заказов** (`event == "заказ"`), оформленных до 10:00 по местному времени, в процентах с одним знаком.

### starter
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
offset = {"PRM": 5, "TMN": 5, "UFA": 5, "KZN": 3}

```

### check
```python
import pandas as _pd
e_ = need('ev', _pd.DataFrame)
assert 'local' in e_.columns, 'В ev нужен столбец local — местное время.'
_e = _pd.read_csv('app_events.csv')
_utc = _pd.to_datetime(_e['ts'], unit='ms')
_off = _e['shop_id'].str[:3].map({'PRM': 5, 'TMN': 5, 'UFA': 5, 'KZN': 3})
_loc = _utc + _pd.to_timedelta(_off, unit='h')
_o = _e['event'] == 'заказ'
_want = round((_loc[_o].dt.hour < 10).mean() * 100, 1)
_got = need('morning_share')
assert not close(_got, round((_utc[_o].dt.hour < 10).mean() * 100, 1), 0.05), f'morning_share = {_got} — так получается по UTC. Переведите время в местное.'
assert not close(_got, round(((_utc + _pd.Timedelta(hours=5))[_o].dt.hour < 10).mean() * 100, 1), 0.05), f'morning_share = {_got}: всем городам прибавлено 5 часов. У Казани смещение 3.'
assert not close(_got, round((_loc.dt.hour < 10).mean() * 100, 1), 0.05), f'morning_share = {_got} — это доля среди всех событий. Нужны только заказы.'
assert close(_got, _want, 0.05), f'morning_share = {_got}, а нужно {_want}.'
_k = e_[e_['shop_id'] == 'KZN-1'].iloc[0]
assert int(_pd.Timestamp(_k['local']).hour) == (int(_pd.to_datetime(_k['ts'], unit='ms').hour) + 3) % 24, 'У казанских кофеен местное время должно быть UTC+3.'
```

### hint
У одного столбца pandas — только один пояс, поэтому `tz_convert` для смеси городов не подходит. Местное время = UTC + смещение города в часах, а смещение у каждой строки своё.

### hint
Код города — `ev["shop_id"].str[:3]`, смещение — `.map(offset)`. Часы в интервал — `pd.to_timedelta(hours, unit="h")`. Затем отберите заказы и возьмите среднее от `local.dt.hour < 10`.

### hint
```python
ev["utc"] = pd.to_datetime(ev["ts"], unit="ms")
hours = ev["shop_id"].str[:3].map(offset)
ev["local"] = ev["utc"] + pd.to_timedelta(hours, unit=...)
orders = ev[ev["event"] == ...]
morning_share = round((orders["local"].dt.hour < 10).mean() * 100, 1)
```

### solution
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
offset = {"PRM": 5, "TMN": 5, "UFA": 5, "KZN": 3}
ev["utc"] = pd.to_datetime(ev["ts"], unit="ms")
hours = ev["shop_id"].str[:3].map(offset)
ev["local"] = ev["utc"] + pd.to_timedelta(hours, unit="h")
orders = ev[ev["event"] == "заказ"]
morning_share = round((orders["local"].dt.hour < 10).mean() * 100, 1)
```

### explain
До 10 утра по местному времени оформлено 26.3 % заказов из приложения — утренний кофе по дороге на работу. По UTC вышло бы 55.8 %: больше половины «утренних» заказов на самом деле дневные. А если всем городам прибавить 5 часов, Казань сдвинется на лишние 2 часа и доля упадёт до 15.6 %. Одна строка со словарём смещений — и три разных ответа на один вопрос; поэтому пояс — первое, что выясняют о любом столбце со временем.
