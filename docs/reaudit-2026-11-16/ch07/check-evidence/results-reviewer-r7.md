# Приёмка адресной правки R7

26/26 ожидаемых вердиктов совпали с фактом в CPython; затем 26/26 — в комплектном Pyodide. Запуски последовательные, переменные OMP/OPENBLAS/MKL_NUM_THREADS=1. Прежние 81 здесь не повторялись; расширенный исполнимый набор 107 подготовлен отдельно.

| Проба | Ожидалось | CPython после | Pyodide после | Pyodide до у рецензента |
|---|---|---|---|---|
| `R7-reverse-visible-full` | зачёт | зачёт | зачёт | отказ |
| `R7-marker-transparent` | отказ | отказ | отказ | зачёт |
| `R7-marker-own-color` | зачёт | зачёт | зачёт | отказ |
| `R7-label-transparent-rgba` | отказ | отказ | отказ | зачёт |
| `R7-duplicate-diagonal-instead-roc` | отказ | отказ | отказ | отказ |
| `R7-extra-reduced-vertex` | зачёт | зачёт | зачёт | зачёт |
| `R7-pr-row-permutation` | зачёт | зачёт | зачёт | зачёт |
| `R7-pr-label-permutation` | отказ | отказ | отказ | отказ |
| `R7-pipe-split-swapped` | отказ | отказ | отказ | отказ |
| `R7-pipe-submitted-incorrect-holdout-labels` | отказ | отказ | отказ | зачёт |
| `R7-pipe-columns-reversed` | зачёт | зачёт | зачёт | зачёт |
| `R7-serialize-compressed` | зачёт | зачёт | зачёт | зачёт |
| `R7-serialize-wrong-object` | отказ | отказ | отказ | отказ |
| `R7-queue-model-padded` | отказ | отказ | отказ | отказ |
| `R7-queue-rule-equal-length-wrong-id` | отказ | отказ | отказ | отказ |
| `R7-metric-wrong-pipeline` | отказ | отказ | отказ | отказ |
| `R7-queue-nsmallest-negative` | зачёт | зачёт | зачёт | зачёт |
| `R7-unordered-scatter` | зачёт | зачёт | зачёт | отказ |
| `R7-line-reverse-diagonal` | зачёт | зачёт | зачёт | отказ |
| `R7-tie-uneven-ids` | зачёт | зачёт | зачёт | зачёт |
| `R7-tie-wrong-row-order` | отказ | отказ | отказ | отказ |
| `R7-content-X` | отказ | отказ | отказ | новый вариант |
| `R7-content-X_train` | отказ | отказ | отказ | новый вариант |
| `R7-content-X_test` | отказ | отказ | отказ | новый вариант |
| `R7-content-y` | отказ | отказ | отказ | новый вариант |
| `R7-content-y_train` | отказ | отказ | отказ | новый вариант |
