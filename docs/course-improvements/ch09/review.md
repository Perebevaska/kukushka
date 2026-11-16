# Глава 9. Независимая предметная проверка

## Исходная редакция

Проверены только алгебраические и вычислительные задания. Выдуманное ускорение при двукратном вызове одного цикла, нулевая матрица Грама и повторное обучение только на исходной матрице проходят. Корректный устойчивый способ lstsq принят. Для приёмки получить векторы прогнозов отдельно из двух обученных моделей и проверить работу таймера при доступной точности.

14 ноября 2026 г. выполнены 13 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch09/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `b69037cf36059184`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
02-matrices/gram correct full matrix true
02-matrices/gram use NumPy Gram and covariance shortcuts true
02-matrices/gram zero out Gram matrix true
02b-vectorize/vectorize reference loop and vectorized algorithm true
02b-vectorize/vectorize call the exact loop twice and fabricate speedup true
03-normal-equation/my-ols stable direct least squares true
03-normal-equation/many-solutions least squares solution true
03-normal-equation/many-solutions two zero-fit-equivalent non-optimal weight vectors true
03b-own-model/my-class train via least squares on the original matrix true
03b-own-model/my-class predict without intercept false predict на игрушке должен дать 11.5 и 0.5: X @ coef_ + intercept_.
05-project/key inverse-free reconstruction true
05-project/hidden-quality fit open model only true
05-project/hidden-quality reference holdout true
```

[Предыдущая рецензия](../../audit-2026-11-13/ch09/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch09) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 13 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch09_acceptance.py); зарегистрировано 5 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch09/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch09) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S09-01 | Исправлено. Вывод ограничен обычной регрессией без штрафа. Объяснение и тест отличают изменение задачи для Ridge и деревьев. |
| S09-02 | Исправлено. Студент верно ответил на изменённые вопросы о ранге и координатах; в тексте названы условия единственности. |
| S09-03 | Исправлено. Две независимо обученные модели проверяют по прогнозам. Ученик получил максимальную разность порядка 7,4·10⁻¹² и разобрал новую анкету. |
| S09-04 | Исправлено по исполнимой проверке времени. При контролируемых тиках реальный ноль принимается, постоянный ноль отвергается. Рецензент повторил дословно исходную попытку №1 из student.jsonl в чистом профиле Chrome 157.0.8103.78: тот же код, кнопка «Проверить», ответ «Отлично, задача решена». Это повтор рецензента; длительность отдельного реального тика браузер в ответе не показывает. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Предметные пробы проведены для матриц, регрессии и измерения времени. После исправления нулевая матрица G отклонена; np.cov в корректной реализации принят. Проверка вызвала обе модели и выявила повторное обучение только на исходных данных. Контролируемый ноль таймера получен нативно.

| Задание и вариант | До | После |
|---|---|---|
| `02-matrices/gram correct full matrix` | зачёт | зачёт |
| `02-matrices/gram use NumPy Gram and covariance shortcuts` | зачёт | зачёт |
| `02-matrices/gram zero out Gram matrix` | зачёт | отказ |
| `02b-vectorize/vectorize reference loop and vectorized algorithm` | зачёт | зачёт |
| `02b-vectorize/vectorize call the exact loop twice and fabricate speedup` | зачёт | отказ |
| `03-normal-equation/my-ols stable direct least squares` | зачёт | зачёт |
| `03-normal-equation/many-solutions least squares solution` | зачёт | зачёт |
| `03-normal-equation/many-solutions two zero-fit-equivalent non-optimal weight vectors` | зачёт | зачёт |
| `03b-own-model/my-class train via least squares on the original matrix` | зачёт | зачёт |
| `03b-own-model/my-class predict without intercept` | отказ | отказ |
| `05-project/key inverse-free reconstruction` | зачёт | зачёт |
| `05-project/hidden-quality fit open model only` | зачёт | отказ |
| `05-project/hidden-quality reference holdout` | зачёт | зачёт |
