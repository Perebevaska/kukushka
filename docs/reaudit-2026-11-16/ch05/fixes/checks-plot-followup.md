# Дополнительная приёмка двух графических проверок

По новым замечаниям независимого рецензента исправлены только `04-confidence/errorbars`, `09-project/chart` и общий включаемый фрагмент `tools/checks/ch05_plot_identity.py`. Видимые условия, исходные CSV и сайт не менялись. Источник готов к сборке координатором.

## До и после

Независимо повторены сохранённые **21** программы рецензента вместе с прежними **37** программами критика в CPython и Pyodide. Исходники старых проверок зафиксированы в [plot-before-course.json](../check-evidence/plot-before-course.json); коды рецензента перенесены из `review-probes-before.json` без редактирования в [review-cases.json](../check-evidence/review-cases.json).

| Наблюдение | Ожидание | До, обе среды | После, обе среды |
|---|---|---|---|
| errorbars: подписи кофеен переставлены отдельно от точек и интервалов | отказ | зачёт | отказ |
| chart: столбцы, значения, подписи и интервалы целиком переставлены B,A | зачёт | отказ | зачёт |
| chart: только X-подписи заменены на B,A при прежних данных A,B | отказ | зачёт | отказ |
| chart: все LineCollection усов и линии скрыты set_visible(False) | отказ | зачёт | отказ |

Исходный прогон: [CPython, 58](../check-evidence/plot-before-native.jsonl), [Pyodide, 58](../check-evidence/plot-before-pyodide.jsonl). Четыре расхождения в каждой среде.

После правки: [CPython, **58/58**](../check-evidence/plot-current-native.jsonl), [Pyodide, **58/58**](../check-evidence/plot-current-pyodide.jsonl). Эти числа включают отдельно 37 прежних проб и 21 новую программу рецензента, а не самостоятельные сдачи ученика.

## Почему правка сохраняет альтернативы

После реального canvas.draw() проверка считывает видимые X-подписи и их позиции, затем сопоставляет с ними точки/столбцы, числовые подписи и интервалы в координатах отрисовки. Порядок создания artists и числовые координаты X не фиксированы. Для errorbars сохранено явно заданное условием возрастание долей на оси X.

Усы проверяются по видимым LineCollection **и** отдельным Line2D: учитываются visible, alpha, альфа цвета, толщина, тип линии и попадание концов в видимую область. Наличие скрытого artist не доказывает наличия видимых усов. Числовые подписи chart привязываются к ближайшему собственному столбцу по фактической позиции текста; значение сверяется по имени группы на оси.

Дополнительно проверены **8** способов представления и ошибок: числовые X с явными подписями в обеих карточках; отдельные vlines для chart; отдельные plot-линии для усов errorbars; прозрачность alpha=0 и RGBA=0; скрытые усы; скрытые точки. Все **8/8** дают ожидаемые ответы в [CPython](../check-evidence/plot-extra-native.jsonl) и [Pyodide](../check-evidence/plot-extra-pyodide.jsonl). [Коды](../check-evidence/plot-extra-cases.json).

## Повторение

Из корня репозитория без сборки сайта:

```sh
PYTHONPATH=.venv/lib/python3.12/site-packages /private/tmp/ku-audit/nb-env/bin/python docs/reaudit-2026-11-16/ch05/check-evidence/run_native.py docs/reaudit-2026-11-16/ch05/check-evidence/current-course.json /private/tmp/ch05-followup-native.jsonl '' docs/reaudit-2026-11-16/ch05/check-evidence/followup-cases.json
node docs/reaudit-2026-11-16/ch05/check-evidence/run_pyodide.mjs docs/reaudit-2026-11-16/ch05/check-evidence/current-course.json /private/tmp/ch05-followup-pyodide.jsonl '' docs/reaudit-2026-11-16/ch05/check-evidence/followup-cases.json
```

Для воспроизведения «до» замените current-course.json на plot-before-course.json; для дополнительных восьми проб замените followup-cases.json на plot-extra-cases.json. Сверяйте `matches` в JSONL. Полный штатный прогон опубликованных страниц и повтор ученика после сборки ведёт координатор.
