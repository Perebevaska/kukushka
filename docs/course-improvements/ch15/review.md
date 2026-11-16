# Глава 15. Независимая предметная проверка

## Исходная редакция

При проверке экспорта финального проекта Pyodide принял город, заменённый для каждого звонка; полностью посторонний ID отвергнут. Перестановка меток ухода между реальными офисами без изменения малого примера также принята. Функция фактических признаков, возвращающая одни NaN, получила зачёт. После редакции нужно восстановить метки и ID по датам в базе, вызвать предъявленную функцию и открыть переданный список именно в дереве из брифа.

14 ноября 2026 г. выполнены 24 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch15/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `733c7f78282d4618`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
01-artifact/decide reference true
01-artifact/decide same comparison with threshold on the left true
01-artifact/decide reverse threshold false in_campaign — сравнение неокруглённой вероятности с card["threshold"].
02-service/validate reference range validator true
02-service/validate allow invalid upper share false Для запроса с изменениями {'delivery_share': 0.04} ошибки должны быть про ['delivery_share'], а сейчас: [].
02b-service-run/tests-write correct alternative boundary cases true
02b-service-run/tests-write omit boolean regression false Ни один случай не ловит predict_bug_bool: добавьте запрос, где app (или другое целое поле) равно True, с ожиданием 422.
03-experiments/paired correct reversed operands true
03-experiments/paired reverse difference false diff — поэлементная разность AUC по фолдам: лес − регрессия (одинаковые фолды CV!).
04-deploy/cron-match reference + two dates satisfying real cron true
04-deploy/cron-match drop weekday filter false cron_match('30 6 * * 1', 2026-11-03 06:30:00) должно быть False.
05-project/slow reference figure true
05-project/slow remove all latency observations and the SLA line from figure false Нужны две группы точек — по одной на версию модели: ax.scatter(...) в цикле по версиям.
05-project/kopecks model aggregate units alternative true
05-project/kopecks invert rubles/kopecks false ratio_32 = 0.
06-final-project/target correct calendar offset true
06-final-project/target old off-by-one DateOffset false build_target('2026-01-15', months=3): ушедших 59, а нужно 46. Окно — до срез + pd.offsets.MonthEnd(months) включительно.
06-final-project/target shuffle real labels among client IDs; small synthetic fixture intact true
06-final-project/features reference features true
06-final-project/models reference grouped AUC in WASM true
06-final-project/features post-check mutation: return all NaNs for actual office features true
06-final-project/package reference package true
06-final-project/package wrong CRM city for every call true
06-final-project/package wrong CRM ID for every call false В call_list.csv 65 клиентов; нужен список с exp_profit > 0 по убыванию exp_profit (их 65).
```

[Предыдущая рецензия](../../audit-2026-11-13/ch15/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch15) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 24 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch15_acceptance.py); зарегистрировано 8 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch15/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch15) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S15-01 | Исправлено. Кратность считается из байтов перед округлением отображаемых КиБ; пример 1250 и 250000 байт даёт 200. |
| S15-02 | Исправлено в условии и заготовке. Актуальный файл export_14.csv и схема calls_to_log названы до попытки; повторная обработка входит в рубрику. |
| S15-03 | Исправлено. На значениях двух окон (−20,0) получается 1,0526; в (0,0) и (−1,0) определено поведение. Безусловное обещание диапазона удалено. |
| S15-04 | Исправлено по опубликованному нативному запуску координатора. Собственная модель загружена из реестра по alias, зарегистрированная версия 1, максимальная разница вероятностей 0,0. |
| S15-05 | Исправлено по чистой сдаче координатора и независимым контрпримерам. В новой папке все семь проверок выполнены, подмена города или ID отклонена. У настоящего повторного запуска осталось одно предупреждение в ячейке 12. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Календарь проверен содержательной заменой обоих MonthEnd на DateOffset: отвергнута по меткам ID. Прежняя автоматическая замена лишь первого вхождения теперь меняет проверку зрелости и потому принимается для наблюдённых дат. Присвоение NaN всем признакам, подмена города или ID отклонены. Ученик получил зачёт за календарную цель, чувствительность списка и комплект файлов. Чистый выпускной блокнот (7/7), API и MLflow исполнял координатор; отдельного запуска в Docker предметный рецензент не делал.

| Задание и вариант | До | После |
|---|---|---|
| `01-artifact/decide reference` | зачёт | зачёт |
| `01-artifact/decide same comparison with threshold on the left` | зачёт | зачёт |
| `01-artifact/decide reverse threshold` | отказ | отказ |
| `02-service/validate reference range validator` | зачёт | зачёт |
| `02-service/validate allow invalid upper share` | отказ | отказ |
| `02b-service-run/tests-write correct alternative boundary cases` | зачёт | зачёт |
| `02b-service-run/tests-write omit boolean regression` | отказ | отказ |
| `03-experiments/paired correct reversed operands` | зачёт | зачёт |
| `03-experiments/paired reverse difference` | отказ | отказ |
| `04-deploy/cron-match reference + two dates satisfying real cron` | зачёт | зачёт |
| `04-deploy/cron-match drop weekday filter` | отказ | отказ |
| `05-project/slow reference figure` | зачёт | зачёт |
| `05-project/slow remove all latency observations and the SLA line from figure` | отказ | отказ |
| `05-project/kopecks model aggregate units alternative` | зачёт | зачёт |
| `05-project/kopecks invert rubles/kopecks` | отказ | отказ |
| `06-final-project/target correct calendar offset` | зачёт | зачёт |
| `06-final-project/target old off-by-one DateOffset` | отказ | зачёт |
| `06-final-project/target shuffle real labels among client IDs; small synthetic fixture intact` | зачёт | отказ |
| `06-final-project/features reference features` | зачёт | зачёт |
| `06-final-project/models reference grouped AUC in WASM` | зачёт | зачёт |
| `06-final-project/features post-check mutation: return all NaNs for actual office features` | зачёт | отказ |
| `06-final-project/package reference package` | зачёт | зачёт |
| `06-final-project/package wrong CRM city for every call` | зачёт | отказ |
| `06-final-project/package wrong CRM ID for every call` | отказ | отказ |
