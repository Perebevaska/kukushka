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

**Пример.** В сутках 86 400 секунд, поэтому `86400` — это `1970-01-02 00:00`, ровно сутки после начала отсчёта. А `1791100800` — `2026-10-04 08:00` по UTC. Проверим кодом — для перевода есть параметр `unit`:

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

{{practice: unix-range}}

### UTC → местное время

В данных урока — события приложения за неделю, `app_events.csv`: номер события, время `ts`, кофейня, гость и тип события (`вход`, `корзина`, `заказ`):

```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
ev.head(3)
```

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

{{practice: p-tz, unix, tmn-fix, local-time}}

## Практика

## task: unix-range | Неделя событий | warmup

В `app_events.csv` время `ts` — unix-время в **миллисекундах**. Сохраните в `first_utc` и `last_utc` дату-время самого раннего и самого позднего события (по UTC, без пояса).

### starter
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")

```

### check
```python
import pandas as _pd
_e = _pd.read_csv('app_events.csv')
_f, _l = _pd.to_datetime(_e['ts'].min(), unit='ms'), _pd.to_datetime(_e['ts'].max(), unit='ms')
_a = _pd.Timestamp(need('first_utc')); _b = _pd.Timestamp(need('last_utc'))
assert _a.year == 2026 and _b.year == 2026, f'first_utc = {_a}, last_utc = {_b}. Проверьте единицу: 13 цифр — миллисекунды, unit="ms".'
assert _a == _f, f'first_utc = {_a} — это не самое раннее событие. Нужен минимум ts.'
assert _b == _l, f'last_utc = {_b} — это не самое позднее событие. Нужен максимум ts.'
```

### hint
Сначала найдите наименьшее и наибольшее число в `ts` (`min()`, `max()`), потом переведите каждое в дату.

### hint
`pd.to_datetime(ev["ts"].min(), unit="ms")` — и так же для `max()`. Можно и наоборот: перевести весь столбец, потом взять `min()` и `max()`.

### solution
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
first_utc = pd.to_datetime(ev["ts"].min(), unit="ms")
last_utc = pd.to_datetime(ev["ts"].max(), unit="ms")
```

### explain
События — с `2026-10-05 02:26` до `2026-10-11 17:24` по UTC, ровно неделя с понедельника по воскресенье. 02:26 ночи по UTC — это 07:26 по Перми: первое событие недели — утренний кофе, а не ночной заказ.

## task: p-tz | Соберите час пик Казани | warmup

Соберите программу: она переводит события казанских кофеен в местное время (UTC+3) и выводит самый частый час по местному времени.

### parsons
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
kzn = ev[ev["shop_id"].str.startswith("KZN")].copy()
kzn["utc"] = pd.to_datetime(kzn["ts"], unit="ms")
kzn["local"] = kzn["utc"].dt.tz_localize("UTC").dt.tz_convert("+03:00")
print(kzn["local"].dt.hour.value_counts().idxmax())
```

### check
```python
import pandas as _pd
_e = _pd.read_csv('app_events.csv')
_k = _pd.to_datetime(_e.loc[_e['shop_id'].str.startswith('KZN'), 'ts'], unit='ms') + _pd.Timedelta(hours=3)
_h = int(_k.dt.hour.value_counts().idxmax())
assert _lines == [str(_h)], f'Должно вывестись {_h}. Сейчас: {_lines}'
```

### hint
Порядок такой же, как в теории: отобрать город → число в дату → приписать UTC → перевести в местный пояс → посчитать.

### hint
Сначала `tz_localize("UTC")`, потом `tz_convert("+03:00")`: переводить можно только время, у которого уже есть пояс.

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

## task: tmn-fix | Почините перевод времени | base

Коллега считал, какая доля событий тюменской кофейни приходится на утро — до 10:00 по местному времени (UTC+5). Ответ у него вышел больше половины, и это подозрительно. Найдите ошибку в заготовке и почините её: `tmn["local"]` — тюменское время, `tmn_morning` — доля событий до 10:00 в процентах с одним знаком.

### starter
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
tmn = ev[ev["shop_id"].str.startswith("TMN")].copy()
tmn["utc"] = pd.to_datetime(tmn["ts"], unit="ms")
tmn["local"] = tmn["utc"].dt.tz_localize("+05:00")
tmn_morning = round((tmn["local"].dt.hour < 10).mean() * 100, 1)
print(tmn_morning)
```

### check
```python
import pandas as _pd
_e = _pd.read_csv('app_events.csv')
_t = _pd.to_datetime(_e.loc[_e['shop_id'].str.startswith('TMN'), 'ts'], unit='ms')
_want = round(((_t + _pd.Timedelta(hours=5)).dt.hour < 10).mean() * 100, 1)
_bad = round((_t.dt.hour < 10).mean() * 100, 1)
tm = need('tmn', _pd.DataFrame)
assert 'local' in tm.columns, 'В tmn нужен столбец local.'
assert int(_pd.Timestamp(tm['local'].iloc[0]).hour) == (int(_t.iloc[0].hour) + 5) % 24, 'Часы в local не сдвинулись: tz_localize только подписывает пояс. Сначала tz_localize("UTC"), потом tz_convert("+05:00").'
assert not close(need('tmn_morning'), _bad, 0.05), f'tmn_morning = {need("tmn_morning")} — это доля по часам UTC.'
assert close(need('tmn_morning'), _want, 0.05), f'tmn_morning = {need("tmn_morning")}, а нужно {_want}.'
```

### hint
Посмотрите на первую строку: `tmn[["utc", "local"]].head(1)`. Часы в `utc` и `local` одинаковые — значит, время не перевели, а только подписали.

### hint
`tz_localize` говорит, в каком поясе время **записано**, — это UTC. Переводит в другой пояс `tz_convert`: `tmn["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")`.

### solution
```python
import pandas as pd
ev = pd.read_csv("app_events.csv")
tmn = ev[ev["shop_id"].str.startswith("TMN")].copy()
tmn["utc"] = pd.to_datetime(tmn["ts"], unit="ms")
tmn["local"] = tmn["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")
tmn_morning = round((tmn["local"].dt.hour < 10).mean() * 100, 1)
print(tmn_morning)
```

### explain
До 10 утра по тюменскому времени — 24.9 % событий, а не 60.6 %, как вышло у коллеги. `tz_localize("+05:00")` не сдвинул часы, а объявил время UTC тюменским: первое событие `08:18` по Тюмени превратилось в `03:18+05:00`. Подпись стала правильной, а момент — на 5 часов раньше настоящего.

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
