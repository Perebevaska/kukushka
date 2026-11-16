# Глава 5. Независимая предметная проверка

## Исходная редакция

Корректный бутстрэп индексов отклонён. Проверка приняла выдуманный интервал вокруг медианы, нулевые усы вместо интервалов Уилсона и отрицательные p-value в двух упражнениях. В decision крайний сценарий падения выручки на 30% уже отличает универсальный совет продлить эксперимент. Для приёмки следует пересчитать концы интервала, подписать единицу назначения и сравнить интервал разности с заранее заданным порогом.

Независимая сверка ab_promise.csv даёт в A 3 924 уникальные сессии, 1 365 заказов и 709 оценок, в B — 3 971, 1 301 и 729 соответственно. При расчёте конверсии знаменатель — число сессий; при расчёте доли низких оценок среди ответивших — число оценок.

14 ноября 2026 г. выполнены 21 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch05/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `76521f2350db5e4e`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
01-probability/running reference true
01-probability/running wrong horizontal constant true
02-distributions/poisson-queue off by one false sf(4, …) — это «больше 4», то есть 5 и больше. «4 и больше» = sf(3, …).
04-confidence/bootstrap reference true
04-confidence/bootstrap valid bootstrap by index false Перевыборка — с возвращением: rng.choice(t, size=len(t), replace=True).
04-confidence/bootstrap incorrect 50 percent CI false Интервал 32.0–32.0 не похож на бутстрэп-ДИ медианы: он должен накрывать медиану и быть шириной в пару минут.
04-confidence/bootstrap invented narrow CI true
04-confidence/errorbars zero uncertainties true
05-hypotheses/perm-snow negative p and degenerate null true
05-hypotheses/perm-fn finite MC corrected true
05-hypotheses/perm-fn inverted res p true
06-tests/agree substitute asymptotic p for simulated true
07-ab/ztest unrounded p false p_value = 0.00856026498422051, а нужно 0.0086.
07-ab/ab-report generic true
07-ab/ab-report ignores metric name true
09-project/late negative p true
09-project/cities all unadjusted p are one true
09-project/chart Wilson true
09-project/chart zero-length Wilson whiskers true
09-project/decision three outcomes true
09-project/decision always extend false выручка B упала на 30 %: decision = 'продлить тест', а нужно 'не внедрять'.
```

[Предыдущая рецензия](../../audit-2026-11-13/ch05/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch05) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 21 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch05_acceptance.py); зарегистрировано 7 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch05/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch05) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S05-01 | Исправлено в показе вероятностей. Суммировать следует точные значения, подставляя p=0,34; независимое округление трёх исходов способно дать 1,001. |
| S05-02 | Исправлено в выводе о снеге. Избыток посчитан относительно ожидаемого при независимости. Различия в длине маршрутов требуют отдельной проверки. |
| S05-03 | Исправлено. choose задаёт цель сравнения до выбора теста; равенство средних не влечёт равенства ранговых распределений. |
| S05-04 | Исправлено. Студент до отправки разделил назначенные сессии, заказы и ответы. У A 3924 сессии и 709 оценок, у B 3971 и 729. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Нулевые усы и выдуманные интервалы отклонены, бутстрэп по индексам принят. После независимой сверки также отклоняются отрицательные проектные p-value и подмена всех исходных p в городах. В дополнительных карточках самодельная константа running, имя метрики в ab-report и присвоение асимптотического p перестановочному всё ещё могут дать зачёт.

| Задание и вариант | До | После |
|---|---|---|
| `01-probability/running reference` | зачёт | зачёт |
| `01-probability/running wrong horizontal constant` | зачёт | зачёт |
| `02-distributions/poisson-queue off by one` | отказ | отказ |
| `04-confidence/bootstrap reference` | зачёт | зачёт |
| `04-confidence/bootstrap valid bootstrap by index` | отказ | зачёт |
| `04-confidence/bootstrap incorrect 50 percent CI` | отказ | отказ |
| `04-confidence/bootstrap invented narrow CI` | зачёт | отказ |
| `04-confidence/errorbars zero uncertainties` | зачёт | отказ |
| `05-hypotheses/perm-snow negative p and degenerate null` | зачёт | отказ |
| `05-hypotheses/perm-fn finite MC corrected` | зачёт | зачёт |
| `05-hypotheses/perm-fn inverted res p` | зачёт | отказ |
| `06-tests/agree substitute asymptotic p for simulated` | зачёт | зачёт |
| `07-ab/ztest unrounded p` | отказ | отказ |
| `07-ab/ab-report generic` | зачёт | зачёт |
| `07-ab/ab-report ignores metric name` | зачёт | зачёт |
| `09-project/late negative p` | зачёт | отказ |
| `09-project/cities all unadjusted p are one` | зачёт | отказ |
| `09-project/chart Wilson` | зачёт | зачёт |
| `09-project/chart zero-length Wilson whiskers` | зачёт | отказ |
| `09-project/decision three outcomes` | зачёт | зачёт |
| `09-project/decision always extend` | отказ | отказ |
