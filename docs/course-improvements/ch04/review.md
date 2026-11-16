# Глава 4. Независимая предметная проверка

## Исходная редакция

Перестановка порядка корректно подписанных колонок walkers отклонена, присвоение неверных подписей принято. Отчёт за 7 октября падает на math.ceil от NaN, обратный знак задержки и нулевой недельный график проходят. После правки нужно проверить группы по названиям, значение actual_min − promised_min по каждой доставке и отсутствие выборки для перцентиля.

14 ноября 2026 г. выполнены 21 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch04/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `fbe4f66876baa200`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
01-plots barh right-default true
01-plots barh right-inverted false Самый популярный должен быть наверху: у barh первый столбец — внизу, поэтому сортируйте по возрастанию.
01-plots bar-shop wrong-labels true
01-plots pandas-plot right-accessor false Нарисуйте через метод plot у Series.
02-histograms hist-km right true
02-histograms hist-km amount-as-km true
06-correlation scatter distance-vs-time true
06-correlation scatter reverse-variables true
07-readable percent-axis right-inverted false Самый большой канал должен быть наверху — у barh это последний столбец. Сортируйте по возрастанию: shares.sort_values().
05b-cohorts heat cohort-image true
05b-cohorts heat fraction-instead-percent false Значения картинки не совпадают с удержанием в процентах.
09-project clean wrong-delay-signed-backwards true
09-project scale right true
09-project scale absolute-time-instead-delay true
09-project walkers right-reference true
09-project walkers correct-order-walkers-first false Значения pv не совпадают. Нужна доля опозданий (aggfunc="mean" по late) × 100; строки — promised_min, столбцы — courier.
09-project walkers wrong-labels true
09-project weekly right true
09-project weekly flat-meaningless-chart true
09-project report reference-one-day false ValueError: cannot convert float NaN to integer
07-readable small-multiples six-case-panels true
```

[Предыдущая рецензия](../../audit-2026-11-13/ch04/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch04) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 21 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch04_acceptance.py); зарегистрировано 9 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch04/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch04) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S04-01 | Исправлено в разборе. Площадь равна высоте плотности, умноженной на ширину, а знаменатель зависит от показанного диапазона. |
| S04-02 | Исправлено. Условие weekday-sqrt различает неокруглённое expected и steps с одним знаком; отбор loud выполняется по заданным steps. |
| S04-03 | Исправлено. В проекте когорт вывод ограничен удержанием; для решения об окупаемости требуется дополнительная маржа относительно контроля и затраты. |
| S04-04 | Прежний вердикт «скорректировать» сохранён. После правки округляется разность коэффициентов; гипотезу о невозможности Спирмена в браузере старое ревью уже отклонило. |
| S04-05 | Исправлено. Для 36 неопределённых исходов доступны пределы от 441/1877 до 477/1877. Ученик отдельно проверил отсутствие подгруппы и пустой отчёт. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Исправлены проектные знак, числа недель и пустая подгруппа. Сохранились дополнительные отказы корректных invert_yaxis и Series.plot.bar и ложный зачёт для подмены осей scatter, подписей bar-shop и суммы вместо расстояний в hist-km. Они относятся к ранним карточкам, отдельно от строгой проверки title и отчёта проекта.

| Задание и вариант | До | После |
|---|---|---|
| `01-plots barh right-default` | зачёт | зачёт |
| `01-plots barh right-inverted` | отказ | отказ |
| `01-plots bar-shop wrong-labels` | зачёт | зачёт |
| `01-plots pandas-plot right-accessor` | отказ | отказ |
| `02-histograms hist-km right` | зачёт | зачёт |
| `02-histograms hist-km amount-as-km` | зачёт | зачёт |
| `06-correlation scatter distance-vs-time` | зачёт | зачёт |
| `06-correlation scatter reverse-variables` | зачёт | зачёт |
| `07-readable percent-axis right-inverted` | отказ | отказ |
| `05b-cohorts heat cohort-image` | зачёт | зачёт |
| `05b-cohorts heat fraction-instead-percent` | отказ | отказ |
| `09-project clean wrong-delay-signed-backwards` | зачёт | отказ |
| `09-project scale right` | зачёт | зачёт |
| `09-project scale absolute-time-instead-delay` | зачёт | отказ |
| `09-project walkers right-reference` | зачёт | зачёт |
| `09-project walkers correct-order-walkers-first` | отказ | зачёт |
| `09-project walkers wrong-labels` | зачёт | отказ |
| `09-project weekly right` | зачёт | зачёт |
| `09-project weekly flat-meaningless-chart` | зачёт | отказ |
| `09-project report reference-one-day` | отказ | зачёт |
| `07-readable small-multiples six-case-panels` | зачёт | зачёт |
