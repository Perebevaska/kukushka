# Глава 8. Независимая предметная проверка

## Исходная редакция

Подмена значений в отчёте при сохранении числовых слов, признаки чужих гостей и стратегия без сравнения с органическими покупками приняты. Безобидная замена имени SQLite-параметра на :as_of отклонена. Для приёмки сверить показатели по их именам и гостям по ID на указанную дату. При изменении стоимости и маржи должна изменяться кривая экономического результата.

14 ноября 2026 г. выполнены 17 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch08/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `7a11ce2f14a68fbc`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
02-budget/gains-plot correct curves true
02-budget/gains-plot constant at the 60th point true
04b-segments/report-text correct report true
04b-segments/report-text wrong conclusion, same numeric tokens true
05b-fairness/missed author counts in bundled runtime true
06-project/decision correct maximum acceptable mean true
06-project/decision globally highest mean, ignores risk false choice = 'Екатеринбург'.
06-project/decision equivalent descending sort true
07-final-project/fp-features original named placeholder true
07-final-project/fp-features valid SQLite named placeholder :as_of false Передайте дату среза параметром (:cutoff и params=...), а не вписывайте в текст запроса.
07-final-project/fp-features assign risk features to wrong guests true
07-final-project/fp-curve original thresholds true
07-final-project/fp-curve wrong comparator at exact probability true
07-final-project/fp-curve ignores caller margin and cost true
07-final-project/fp-honest incremental policy true
07-final-project/fp-honest ignores counterfactual when choosing strategy true
07-final-project/fp-honest omits organic purchases from final return false honest_profit = 210572. Вычтите organic × n_send ожидаемых «и так купивших».
```

[Предыдущая рецензия](../../audit-2026-11-13/ch08/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch08) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 17 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch08_acceptance.py); зарегистрировано 6 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch08/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch08) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S08-01 | Исправлено. Конечный реестр и выбор различных адресов согласованы. Нативная проба учитывает отсутствие приемлемого города и граничный риск 2,5%. Противоречие в ранней повторной попытке ученика зафиксировано отдельно. |
| S08-02 | Исправлено в выводе. Совпадение порогов само по себе не подтверждает калибровку. Для проверки нужны вероятности и наблюдаемые частоты у сопоставимых гостей. |
| S08-03 | Исправлено. Студент до разбора самостоятельно выбрал 0,08, получил 791 адресата и 138723 ₽ ожидаемой дополнительной маржи. Он явно указал допущение о контрольной группе. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Новые проверки отклонили чужой morning_share и игнорирование стоимости и границы порога. Привязанные к ключу структурированные показатели report-text проверяются, но противоречивый текст, дописанный к правильной таблице, может получить зачёт; смысл письма читает рецензент. fp-honest допускает обоснованную неотрицательную стратегию и пересчитывает итог с контролем. Числа сами по себе не позволяют установить, что автор учитывал контроль при выборе порога. Фиктивная точка gains-plot также ещё проходит.

| Задание и вариант | До | После |
|---|---|---|
| `02-budget/gains-plot correct curves` | зачёт | зачёт |
| `02-budget/gains-plot constant at the 60th point` | зачёт | зачёт |
| `04b-segments/report-text correct report` | зачёт | зачёт |
| `04b-segments/report-text wrong conclusion, same numeric tokens` | зачёт | зачёт |
| `05b-fairness/missed author counts in bundled runtime` | зачёт | зачёт |
| `06-project/decision correct maximum acceptable mean` | зачёт | зачёт |
| `06-project/decision globally highest mean, ignores risk` | отказ | зачёт |
| `06-project/decision equivalent descending sort` | зачёт | зачёт |
| `07-final-project/fp-features original named placeholder` | зачёт | зачёт |
| `07-final-project/fp-features valid SQLite named placeholder :as_of` | отказ | зачёт |
| `07-final-project/fp-features assign risk features to wrong guests` | зачёт | отказ |
| `07-final-project/fp-curve original thresholds` | зачёт | зачёт |
| `07-final-project/fp-curve wrong comparator at exact probability` | зачёт | отказ |
| `07-final-project/fp-curve ignores caller margin and cost` | зачёт | отказ |
| `07-final-project/fp-honest incremental policy` | зачёт | зачёт |
| `07-final-project/fp-honest ignores counterfactual when choosing strategy` | зачёт | зачёт |
| `07-final-project/fp-honest omits organic purchases from final return` | отказ | отказ |
