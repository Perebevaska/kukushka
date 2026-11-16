# Глава 3. Независимая предметная проверка

## Исходная редакция

У задания mechanism все три допустимых ответа требуют выбрать механизм утраты данных. На CSV у всех 144 гостей без среднего чека ноль визитов. Ответ о неопределённом значении отклонён. В проекте после перемещения возраста между ID и удаления средней выручки одного сегмента всё ещё получен зачёт. У телефона с добавочным номером корректный пропуск отвергнут и в упражнении, и в проекте. Предметный критерий — сверять смысл пропуска, возраст и сегмент по ID, возвращать пропуск для нераспознанного номера.

14 ноября 2026 г. выполнены 16 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch03/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `235ced8ed9bf9d6f`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
05-strings phone10 base true
05-strings phone10 extension-accepted true
05-strings phone10 extension-rightly-masked false Число пропусков изменилось.
09-project clean baseline true
09-project clean correct-rejection-of-extension false Столбец phone не совпадает, например у C1000: nan, а нужно '2345678912'.
09-project age age-of-another-person true
09-project guests alternative-correct true
09-project guests cups-instead-of-orders true
09-project sources one-source-without-revenue true
09-project age-money one-age-band-without-orders true
09-project report correct true
09-project report ignores-raw true
03b-excel auto-header dynamic-index true
03b-excel auto-header hardcoded-counts true
03b-excel auto-header alternative-dynamic-lookup true
02-missing mechanism structural-missing-correct-description false mechanism = 'средний чек не определён без визитов'. Выберите одно из: "MCAR", "MAR", "MNAR".
```

[Предыдущая рецензия](../../audit-2026-11-13/ch03/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch03) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 16 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch03_acceptance.py); зарегистрировано 11 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch03/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch03) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S03-01 | Исправлено. Структурное отсутствие среднего чека теперь даёт зачёт, знаменатель проверен по 144 гостям с нулём визитов. |
| S03-02 | Подтверждено достоинство. Сохранено сообщение born с исходной строкой и требуемой датой. Показ медианы дополнен проверкой привязки по ID. |
| S03-03 | Исправлено. Нативная проба отклонила классификацию «море» и «желаю пропустить» по первой букве. Студент проверил неизвестное значение. |
| S03-04 | Исправлено. Ученик проверил 100 и 101 год. Эталон отделяет границу полных лет от верхней границы интервала. |
| S03-05 | Исправлено. Новое правильное решение объявляет добавочный номер неопределённым и проходит две исторические пробы. Попытка снова отрезать последние десять цифр отклонена в full и clean. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

По одинаковой книге жёсткий словарь высот показывает верный результат; на самой исходной книге автопроверка пропускает такое решение. Нативный перенос с перемещённым заголовком показывает работоспособность динамического решения. Историческое имя extension-accepted теперь означает исполнение исправленной авторской функции, которая оставляет добавочный номер неопределённым.

| Задание и вариант | До | После |
|---|---|---|
| `05-strings phone10 base` | зачёт | зачёт |
| `05-strings phone10 extension-accepted` | зачёт | зачёт |
| `05-strings phone10 extension-rightly-masked` | отказ | зачёт |
| `09-project clean baseline` | зачёт | зачёт |
| `09-project clean correct-rejection-of-extension` | отказ | зачёт |
| `09-project age age-of-another-person` | зачёт | отказ |
| `09-project guests alternative-correct` | зачёт | зачёт |
| `09-project guests cups-instead-of-orders` | зачёт | отказ |
| `09-project sources one-source-without-revenue` | зачёт | отказ |
| `09-project age-money one-age-band-without-orders` | зачёт | отказ |
| `09-project report correct` | зачёт | зачёт |
| `09-project report ignores-raw` | зачёт | отказ |
| `03b-excel auto-header dynamic-index` | зачёт | зачёт |
| `03b-excel auto-header hardcoded-counts` | зачёт | зачёт |
| `03b-excel auto-header alternative-dynamic-lookup` | зачёт | зачёт |
| `02-missing mechanism structural-missing-correct-description` | отказ | зачёт |
