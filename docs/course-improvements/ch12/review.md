# Глава 12. Независимая предметная проверка

## Исходная редакция

Обмен местами равных по длине июля и августа, текущее число заказов вместо лага и предзаданные имена выявленных утечек получают зачёт. Эталонный прогноз с явной подменой чисел проверка final отклоняет. После редакции проверить изменение всего неизвестного на 20:00 хвоста и воспроизвести ровно 24 прогноза без раскрытия будущих заказов.

14 ноября 2026 г. выполнены 20 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch12/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `538d53c767d36db8`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
02-decompose/adf default reference ADF true
02-decompose/adf reversed p-value rule false stationary = ['дни'].
03-features/make-features equivalent rolling then lag true
03-features/make-features current outcome in window false roll_24 — среднее 24 часов ДО текущего: s.shift(1).rolling(24).mean().
03-features/leak-test reference current-target perturbation true
03-features/leak-test hardcode observed leak names for every input true
03b-time-split/check-order reference order true
03b-time-split/check-order compare first dates only false Час 05:00 в обучении позже тестовых 02:00–04:00: функция должна вернуть False.
04-forecast/metrics RMSE via normalized L2 true
04-forecast/metrics forecast in WAPE denominator false Проверьте формулы на [3, 5] и [1, 5]: MAE 1, RMSE √2, WAPE 2/8.
05-project/split reference split true
05-project/split exchange equal-size July and August true
05-project/split current orders in a lag true
05-project/split equivalent dates true
05-project/grid wrong KFold false cv = 3. Для ряда нужен TimeSeriesSplit(n_splits=3), а не число фолдов: cv=3 означает обычный KFold без учёта времени.
05-project/grid TimeSeriesSplit with a safety gap false gs обучен не на train | valid: лучший результат не совпадает с пересчётом на марте–июле.
05-project/final false predictions false pred_test — прогноз HistGradientBoostingRegressor(random_state=0, **best_params), обученного на train | valid, обрезанный нулём.
05-project/staffing reference plan true
05-project/staffing incorrect saved needed vector true
05-project/staffing floor capacity instead of ceiling false модель: short, extra = 0.714, 5.0, а нужно 0.304, 120.0.
```

[Предыдущая рецензия](../../audit-2026-11-13/ch12/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch12) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 20 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch12_acceptance.py); зарегистрировано 2 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch12/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch12) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S12-01 | Исправлено. При изменении неизвестного хвоста вместо одной текущей метки проверка выявляет будущие признаки; законное окно прошлых значений принято. |
| S12-02 | Исправлено. months использует точные средние до округления процентного изменения; отличие 6,4% от 6,3% разобрано на исходном примере. |
| S12-03 | Исправлено. В 20:00 созрели метки по 19:00. Подмена будущего хвоста не должна менять выдачу 24 часов; план и реальная попытка студента разделяют выпуск и оценку. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Текущий спрос в лаге и обмен июля/августа отвергнуты. В исторических мутациях имя старого конструктора grid с gap=0 больше отсутствует; текущий TimeSeriesSplit(gap=28) и ошибочный KFold прогнаны отдельно. После общего исторического прогона координатор добавил проверку needed по каждому часу и назвал deficit и coverage_work в условии. Рецензент заново запустил штатное решение и получил зачёт. Историческая подстановка единиц и дополнительная подстановка нулей обе дали отказ «Проверьте needed для каждого часа теста по порядку». В таблице ниже для этой строки указана последняя нативная перепроверка.

| Задание и вариант | До | После |
|---|---|---|
| `02-decompose/adf default reference ADF` | зачёт | зачёт |
| `02-decompose/adf reversed p-value rule` | отказ | отказ |
| `03-features/make-features equivalent rolling then lag` | зачёт | зачёт |
| `03-features/make-features current outcome in window` | отказ | отказ |
| `03-features/leak-test reference current-target perturbation` | зачёт | зачёт |
| `03-features/leak-test hardcode observed leak names for every input` | зачёт | отказ |
| `03b-time-split/check-order reference order` | зачёт | зачёт |
| `03b-time-split/check-order compare first dates only` | отказ | отказ |
| `04-forecast/metrics RMSE via normalized L2` | зачёт | зачёт |
| `04-forecast/metrics forecast in WAPE denominator` | отказ | отказ |
| `05-project/split reference split` | зачёт | зачёт |
| `05-project/split exchange equal-size July and August` | зачёт | отказ |
| `05-project/split current orders in a lag` | зачёт | отказ |
| `05-project/split equivalent dates` | зачёт | зачёт |
| `05-project/grid wrong KFold` | отказ | изменилась постановка/код |
| `05-project/grid TimeSeriesSplit with a safety gap` | отказ | изменилась постановка/код |
| `05-project/final false predictions` | отказ | отказ |
| `05-project/staffing reference plan` | зачёт | зачёт |
| `05-project/staffing incorrect saved needed vector` | зачёт | отказ после дополнительной правки (на зафиксированном экспорте был зачёт) |
| `05-project/staffing floor capacity instead of ceiling` | отказ | отказ |
