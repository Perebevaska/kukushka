# Глава 11. Независимая предметная проверка

## Исходная редакция

Проект принял одинаковые вероятности всех классов и отрицательные вероятности. В реальном расчёте при исходном общем пороге kNN передаёт оператору 13 цифр, MLP — 37; перехвачено 3 и 6 ошибок соответственно. Сравнение требует одинакового числа мест. Проверка градиента с неверным знаком и численно неустойчивого softmax уже срабатывает правильно.

14 ноября 2026 г. выполнены 17 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch11/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `4977a911284b175b`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
02-backprop/grad-check centered difference and analytic gradient true
02-backprop/grad-check incorrect gradient sign false analytic = 0.40131, а нужно -0.40131.
02b-graph/clip-norm equivalent L2 magnitude true
02b-graph/clip-norm clip coordinate by coordinate false Для [6, 8] с порогом 5 должно выйти [3, 4]: норма 10, вектор уменьшается вдвое целиком.
04b-softmax/softmax scipy implementation true
04b-softmax/softmax exponential overflow false В P есть nan — без сдвига на максимум e^1000 переполняется.
04b-softmax/batches valid permutation true
04b-softmax/batches never shuffle true
04c-debug/dropout inverted mask true
04c-debug/dropout omitted scale false mean_after = 0.703.
04c-debug/batchnorm unbiased running var like PyTorch false run_mean = [0.6433 5.3033 0.    ], run_var = [  2.4333 233.7933   0.81  ]. Проверьте, что второй батч продолжил обновлять скользящие средние после первого.
05-project/look no digit images on axes true
05-project/mlp reference probabilities true
05-project/mlp uniform model scores true
05-project/mlp negative probabilities true
05-project/errors equivalent boolean counts true
05-project/errors fraction errors among sent instead false errors_caught = 0.162.
```

[Предыдущая рецензия](../../audit-2026-11-13/ch11/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch11) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 17 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch11_acceptance.py); зарегистрировано 5 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch11/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch11) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S11-01 | Исправлено. Выбор alpha и эпох отделён от финальной оценки. Своя сеть ученика выдала 450×10 вероятностей, метрика получена по argmax. |
| S11-02 | Исправлено. Оба метода получили бюджет 37 цифр; у ученика после очереди осталось 2 и 4 ошибки. Идентификаторы реальных телефонов отсутствуют. |
| S11-03 | Исправлено по нативному практикуму. Время predict выделено из расчёта ошибки, которому нужен y_test. Отдельной нагрузочной проверки интерфейса в этом прогоне не было. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Отрицательные и равномерные вероятности и отделённые от модели прогнозы отклонены. Дополнительные пробы batches/look ещё принимают отсутствие перемешивания или снимков.

| Задание и вариант | До | После |
|---|---|---|
| `02-backprop/grad-check centered difference and analytic gradient` | зачёт | зачёт |
| `02-backprop/grad-check incorrect gradient sign` | отказ | отказ |
| `02b-graph/clip-norm equivalent L2 magnitude` | зачёт | зачёт |
| `02b-graph/clip-norm clip coordinate by coordinate` | отказ | отказ |
| `04b-softmax/softmax scipy implementation` | зачёт | зачёт |
| `04b-softmax/softmax exponential overflow` | отказ | отказ |
| `04b-softmax/batches valid permutation` | зачёт | зачёт |
| `04b-softmax/batches never shuffle` | зачёт | зачёт |
| `04c-debug/dropout inverted mask` | зачёт | зачёт |
| `04c-debug/dropout omitted scale` | отказ | отказ |
| `04c-debug/batchnorm unbiased running var like PyTorch` | отказ | отказ |
| `05-project/look no digit images on axes` | зачёт | зачёт |
| `05-project/mlp reference probabilities` | зачёт | зачёт |
| `05-project/mlp uniform model scores` | зачёт | отказ |
| `05-project/mlp negative probabilities` | зачёт | отказ |
| `05-project/errors equivalent boolean counts` | зачёт | зачёт |
| `05-project/errors fraction errors among sent instead` | отказ | отказ |
