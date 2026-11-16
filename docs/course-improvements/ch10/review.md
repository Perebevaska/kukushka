# Глава 10. Независимая предметная проверка

## Исходная редакция

Подмена температуры будущей выручкой и инверсия маски train/test при сохранении ожидаемой длины приняты. После вычисления метрики результат прогноза можно заменить нулями, а все длительности в таблице — выдуманным значением. Подлинное алгебраически эквивалентное вычисление градиента проходит. Для приёмки сверить доступность полей на дату выпуска, соответствие дат маске и метрику по предъявленному прогнозу.

14 ноября 2026 г. выполнены 16 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch10/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `81e2897d03a53a83`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
02-gd-many/grad-vec analytic gradient true
02-gd-many/grad-vec sum per-observation gradients true
02-gd-many/grad-vec reversed gradient false g = [-2.         -6.66666667], а нужно [2.    6.667].
02b-optimizers/adam-step bias-corrected true
02b-optimizers/adam-step first moment left uncorrected false Новые веса не сходятся. Проверьте поправку: m / (1 − b1**t), s / (1 − b2**t), и шаг lr · m̂ / (√ŝ + eps).
05-project/split correct chronological mask true
05-project/split use future revenue under weather column true
05-project/split reversed membership with correct counts true
05-project/split same cutoff as boolean expression true
05-project/trend reference trend correction true
05-project/trend equivalent logarithmic subtraction true
05-project/trend zero predicted vector after scoring true
05-project/compare reference quality and time true
05-project/compare fabricated duration in every table row true
06-libraries/speed-table original native-like table true
06-libraries/speed-table fabricated best speed winner true
```

[Предыдущая рецензия](../../audit-2026-11-13/ch10/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch10) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 16 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch10_acceptance.py); зарегистрировано 5 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch10/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch10) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S10-01 | Исправлено. Договорной срок ищут как первую допустимую целую минуту; нативная проверка promise-levels принята и в ученическом журнале есть integer-promise. |
| S10-02 | Исправлено в разборе. Первый шаг Adam для градиентов 0, ε и намного больше ε даёт модули 0, η/2 и около η. Снятие поправки первого момента отклонено. |
| S10-03 | Исправлено в пояснении. Для проверенной версии sklearn 1.8 учтена поддержка NaN лесом; нулевой чек и отсутствие чека различимы. |
| S10-04 | Исправлено. При подмене фактической погоды и будущей выручки разовый план на 1 июля воспроизводится. Инверсия маски отклонена. |
| S10-05 | Исправлено в нативном практикуме. Замеры подбора и финального fit выведены отдельно. Произвольно записанные время и имя победителя в браузерном speed-table остаются слабой проверкой и не служат измерением библиотек. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Перестановка маски и признаки из будущего отклонены. После проверки усилен контроль p_after; нулевой вектор отвергнут при сохранении прежних метрик. У ученика после первой ошибки типа и технических попыток редактора split-fill получил «Отлично, задача решена». Две ранние попытки compare отклонены: апрельская валидация получила X июльского выпуска. После уточнения условия студент заново собрал признаки через prep(s, as_of="2025-04-01"). С первой ранее открытой подсказкой получил «Верно!»; в апреле–июне выбран HistGradientBoosting (RMSE 8,136), финальный RMSE 9,06 и выигрыш к линейной модели 6,93. Замер внешних библиотек относится к выполненному нативному блокноту. В браузерных compare и speed-table возможна подстановка времени и победителя из заранее собранной таблицы.

| Задание и вариант | До | После |
|---|---|---|
| `02-gd-many/grad-vec analytic gradient` | зачёт | зачёт |
| `02-gd-many/grad-vec sum per-observation gradients` | зачёт | зачёт |
| `02-gd-many/grad-vec reversed gradient` | отказ | отказ |
| `02b-optimizers/adam-step bias-corrected` | зачёт | зачёт |
| `02b-optimizers/adam-step first moment left uncorrected` | отказ | отказ |
| `05-project/split correct chronological mask` | зачёт | зачёт |
| `05-project/split use future revenue under weather column` | зачёт | отказ |
| `05-project/split reversed membership with correct counts` | зачёт | отказ |
| `05-project/split same cutoff as boolean expression` | зачёт | зачёт |
| `05-project/trend reference trend correction` | зачёт | зачёт |
| `05-project/trend equivalent logarithmic subtraction` | зачёт | зачёт |
| `05-project/trend zero predicted vector after scoring` | зачёт | отказ |
| `05-project/compare reference quality and time` | зачёт | зачёт |
| `05-project/compare fabricated duration in every table row` | зачёт | зачёт |
| `06-libraries/speed-table original native-like table` | зачёт | зачёт |
| `06-libraries/speed-table fabricated best speed winner` | зачёт | зачёт |
