# Глава 7. Независимая предметная проверка

## Исходная редакция

Порог, выбранный по тесту, действительно отклоняется, корректный Pipeline для масштабирования внутри фолда принимается. Пустой сохранённый файл модели, таблица grid с нулевой оценкой каждой комбинации и отключённая подготовка признаков получают зачёт. Приёмка требует открыть сохранённую модель и пересчитать прогноз на сырой контрольной строке, затем сверить таблицу фолдов с объектом поиска.

14 ноября 2026 г. выполнены 16 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch07/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `3bc32a254df4f76e`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
03b-money-threshold/honest-t validation optimum true
03b-money-threshold/honest-t test optimum false Когда меняются только тестовые гости, t_val меняется (0.1 вместо 0.3). Значит, порог выбран с участием теста. Подбирайте его только по X_val.
03-threshold/roc-plot correct plotted lines true
03-threshold/roc-plot false diagonal has interior (0.5,0.9) true
06b-feature-check/combo scale separately in every fold true
07b-own-steps/group-ratio learned training statistics true
07b-own-steps/group-ratio learn group means again at transform false Средние посчитаны по X_test, а не взяты из fit. В transform используйте self.means_.
09-project/pipe trained preprocessing true
09-project/pipe correct name-based columns, different order false Столбцы X: ['budget_pp', 'channel', 'city', 'company_size', 'days_to_event', 'evening', 'event_type', 'guests', 'hour', 'manager', 'repeat_client', 'response_hours', 'tasting', 'weekday'], а ожидались ['channel', 'event_type', 'city', 'company_size', 'guests', 'budget_pp', 'days_to_event', 'manager', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']. Без get_dummies — сырые столбцы.
09-project/pipe no preprocessing step despite reported scores true
09-project/metric stable sort as alternative to nlargest true
09-project/metric bottom risk false На маленьком примере (10 заявок, договоры у 1-й, 3-й и 6-й) catch_rate вернула 0.3333333333333333, а ожидалось 0.667: в верхние 3 попали два договора из трёх. Проверьте, что индекс Series берётся из y_true.
09-project/grid reported table contains all zero scores true
09-project/final compare exact count selected by the rule true
08-tuning/save-load normal round trip true
08-tuning/save-load saved artifact is empty true
```

[Предыдущая рецензия](../../audit-2026-11-13/ch07/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch07) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 16 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch07_acceptance.py); зарегистрировано 4 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch07/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch07) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S07-01 | Исправлено в объяснении. Для 0,4, 0,4 и 0,9 средняя вероятность 0,567; на пороге 0,5 голос леса положительный. |
| S07-02 | Исправлено. Пример разбирает фолд и два знаменателя. При 34 найденных из 48 и 120 контактах полнота 34/48, точность списка 34/120; равный бюджет закреплён в проекте. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Пустой файл модели, выключенный prep и пропавшие фолдовые оценки отклонены при повторной проверке. Иной порядок именованных признаков принят. Старые текстовые подстановки для metric/final перестали находить прежний код; нативно адаптированные пробы приняли nlargest со стабильным порядком и точное k, отвергли нижние вероятности. У ROC-диагонали по-прежнему недостаточно проверены средние точки.

| Задание и вариант | До | После |
|---|---|---|
| `03b-money-threshold/honest-t validation optimum` | зачёт | зачёт |
| `03b-money-threshold/honest-t test optimum` | отказ | отказ |
| `03-threshold/roc-plot correct plotted lines` | зачёт | зачёт |
| `03-threshold/roc-plot false diagonal has interior (0.5,0.9)` | зачёт | зачёт |
| `06b-feature-check/combo scale separately in every fold` | зачёт | зачёт |
| `07b-own-steps/group-ratio learned training statistics` | зачёт | зачёт |
| `07b-own-steps/group-ratio learn group means again at transform` | отказ | отказ |
| `09-project/pipe trained preprocessing` | зачёт | зачёт |
| `09-project/pipe correct name-based columns, different order` | отказ | зачёт |
| `09-project/pipe no preprocessing step despite reported scores` | зачёт | отказ |
| `09-project/metric stable sort as alternative to nlargest` | зачёт | изменилась постановка/код |
| `09-project/metric bottom risk` | отказ | изменилась постановка/код |
| `09-project/grid reported table contains all zero scores` | зачёт | отказ |
| `09-project/final compare exact count selected by the rule` | зачёт | изменилась постановка/код |
| `08-tuning/save-load normal round trip` | зачёт | зачёт |
| `08-tuning/save-load saved artifact is empty` | зачёт | отказ |
