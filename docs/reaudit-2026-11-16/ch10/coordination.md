# Исходная координаторская сверка главы 10

**Статус: исходная сверка завершена; глава ещё не принята.** Разрешена только глава 10, исходная версия `c637497798d38e3e1e2c56794656c3ccbb940adb`. Координатор: Sol / medium. Прочитаны AGENTS.md, [регламент](../../course-audit.md), строка 10 [плана](../../course-reaudit-plan.md) и [прежний отчёт главы](../../course-improvements/ch10/report.md). План требует дополнительно получателя и критика делового вывода; оба первичных результата присутствуют. Эта сверка читает JSON, CSV, Markdown и SHA стандартной библиотекой Python. Новые ML, Node и Jupyter здесь не запускались.

## Версия и знаменатели

Сверены SHA десяти неизменяемых исходников из `/private/tmp/kuch10round/original/content/ch10/` с [baseline.json](technical/baseline.json). SHA поля `export_sha256` относится к полному экспорту из 2454 записей (`b304009d…`); глава из [baseline-export.json](technical/baseline-export.json) содержит ровно его фильтр ch10, её SHA `1e2b99b8…`. Это разные файлы, а не повреждение контрольной суммы. Текущие изменяемые исходники не использовались для приписывания исходных вердиктов.

| Набор | Состав | Единица |
|---|---|---|
| Штатный исходный экспорт | 57 task + 5 predict + 26 cell = 88 | Авторская задача, предсказание или демонстрационная ячейка |
| Ученический реестр | 57 task + 5 predict + 12 quiz + 14 final = 88 | Отдельный ID для собственной сдачи |
| Фактические сдачи | 91 graded + 2 browserError = 93 | Событие, включая повторы |
| Критик проверок | 36 на каждой поверхности | 4 historical-original + 4 migration + 12 historical-additional + 16 new |
| Рецензент | 18 на каждой поверхности | 17 исходных контрактов + 1 миграция периода |
| Native ученика | 5 публичных процедур + 8 упражнений | Собственные нативные результаты |
| Получатель | 7 проверок | Загрузка модели, новый период, одиночная строка, перестановка, две мутации и чистый refit |

Совпадение двух чисел 88 случайное: экспорт включает 26 демонстраций, реестр — 26 вопросов quiz/final. Множество 57 task сверено точно, множество всех 88 ID реестра равно фактически отправленному; пропусков и лишних ID нет. [Машинная сверка](coordination-initial.json) · [Реестр](technical/inventory.json) · [Штатный stdout](technical/baseline-standard.log). Последний содержит `✓ проверено: 88, проблем: 0`; код возврата этим коротким логом отдельно не доказан.

## Реальные первые и повторные сдачи

Все 88/88 ID в конце приняты (100%). Первое событие принято у 83/88 (94,32%); первая попытка, достигшая проверки курса, — у 85/88 (96,59%). Два различающихся знаменателя сохраняют ошибки транспортной сборки Parsons отдельно от трёх отказов курса. Итоговый тест: 14/14 с первой реальной сдачи. Исходный initial-attempts содержит **91**, а не 93 записи: это только bool-вердикты. Полный multiset объединений input+feedback совпал с initial-attempts после удаления только поля `at`, включая код, choice, expect, visible_output, visible_prompt, feedback, score и кратность повторов. Две browserError в нём отсутствуют; они сохранены в raw.

| Вид ID | Всего | Первое событие принято | Первый graded принят | В конце принято |
|---|---:|---:|---:|---:|
| task | 57 | 52 | 54 | 57 |
| predict | 5 | 5 | 5 | 5 |
| quiz | 12 | 12 | 12 | 12 |
| final_quiz | 14 | 14 | 14 | 14 |

Каждая исходная пара проверена построчно по ID, количеству и полному payload; ссылки дают исходный код/choice и первоначальную реакцию:

| Input | Feedback | Событий | Принято / отказ / transport |
|---|---|---:|---|
| [01-gradient-01-input.jsonl](student/raw/01-gradient-01-input.jsonl) | [01-gradient-01-feedback.jsonl](student/raw/01-gradient-01-feedback.jsonl) | 11 | 10 / 0 / 1 |
| [01-gradient-02-input.jsonl](student/raw/01-gradient-02-input.jsonl) | [01-gradient-02-feedback.jsonl](student/raw/01-gradient-02-feedback.jsonl) | 1 | 1 / 0 / 0 |
| [01b-numeric-01-input.jsonl](student/raw/01b-numeric-01-input.jsonl) | [01b-numeric-01-feedback.jsonl](student/raw/01b-numeric-01-feedback.jsonl) | 8 | 7 / 1 / 0 |
| [01b-numeric-02-input.jsonl](student/raw/01b-numeric-02-input.jsonl) | [01b-numeric-02-feedback.jsonl](student/raw/01b-numeric-02-feedback.jsonl) | 1 | 1 / 0 / 0 |
| [02-gd-many-01-input.jsonl](student/raw/02-gd-many-01-input.jsonl) | [02-gd-many-01-feedback.jsonl](student/raw/02-gd-many-01-feedback.jsonl) | 12 | 11 / 0 / 1 |
| [02-gd-many-02-input.jsonl](student/raw/02-gd-many-02-input.jsonl) | [02-gd-many-02-feedback.jsonl](student/raw/02-gd-many-02-feedback.jsonl) | 1 | 1 / 0 / 0 |
| [02b-optimizers-01-input.jsonl](student/raw/02b-optimizers-01-input.jsonl) | [02b-optimizers-01-feedback.jsonl](student/raw/02b-optimizers-01-feedback.jsonl) | 7 | 7 / 0 / 0 |
| [03-boosting-reviewed-input.jsonl](student/raw/03-boosting-reviewed-input.jsonl) | [03-boosting-reviewed-feedback.jsonl](student/raw/03-boosting-reviewed-feedback.jsonl) | 12 | 12 / 0 / 0 |
| [04-tuning-reviewed-input.jsonl](student/raw/04-tuning-reviewed-input.jsonl) | [04-tuning-reviewed-feedback.jsonl](student/raw/04-tuning-reviewed-feedback.jsonl) | 12 | 12 / 0 / 0 |
| [05-project-01-input.jsonl](student/raw/05-project-01-input.jsonl) | [05-project-01-feedback.jsonl](student/raw/05-project-01-feedback.jsonl) | 10 | 8 / 2 / 0 |
| [05-project-02-input.jsonl](student/raw/05-project-02-input.jsonl) | [05-project-02-feedback.jsonl](student/raw/05-project-02-feedback.jsonl) | 2 | 2 / 0 / 0 |
| [06-libraries-01-input.jsonl](student/raw/06-libraries-01-input.jsonl) | [06-libraries-01-feedback.jsonl](student/raw/06-libraries-01-feedback.jsonl) | 2 | 2 / 0 / 0 |
| [test-01-input.jsonl](student/raw/test-01-input.jsonl) | [test-01-feedback.jsonl](student/raw/test-01-feedback.jsonl) | 14 | 14 / 0 / 0 |

Несданные [03-boosting-01-input](student/raw/03-boosting-01-input.jsonl) и [04-tuning-01-input](student/raw/04-tuning-01-input.jsonl) — по 12 черновиков без feedback. Они исключены из событий; reviewed-input — первая реальная сдача после самостоятельной редакции. Это не 24 дополнительных попытки.

### Пять событий с ошибками

- `01-gradient/p-gd`: [student/raw/01-gradient-01-input.jsonl:3](student/raw/01-gradient-01-input.jsonl) → [student/raw/01-gradient-01-feedback.jsonl:3](student/raw/01-gradient-01-feedback.jsonl). `Error: Нет соответствующей строки Parsons: x=np.array([1.,2.,3.]); y=np.array([2.,4.,6.])`. Код и `expect` до сдачи сохранены в input; полный текст реакции и SHA кода — в [JSON](coordination-initial.json).
- `01b-numeric/bisect`: [student/raw/01b-numeric-01-input.jsonl:4](student/raw/01b-numeric-01-input.jsonl) → [student/raw/01b-numeric-01-feedback.jsonl:4](student/raw/01b-numeric-01-feedback.jsonl). `NameError: name 'grad' is not defined`. Код и `expect` до сдачи сохранены в input; полный текст реакции и SHA кода — в [JSON](coordination-initial.json).
- `02-gd-many/p-batch`: [student/raw/02-gd-many-01-input.jsonl:3](student/raw/02-gd-many-01-input.jsonl) → [student/raw/02-gd-many-01-feedback.jsonl:3](student/raw/02-gd-many-01-feedback.jsonl). `Error: locator.evaluate: Error: отступ вне шага`. Код и `expect` до сдачи сохранены в input; полный текст реакции и SHA кода — в [JSON](coordination-initial.json).
- `05-project/split`: [student/raw/05-project-01-input.jsonl:2](student/raw/05-project-01-input.jsonl) → [student/raw/05-project-01-feedback.jsonl:2](student/raw/05-project-01-feedback.jsonl). `TypeError: Invalid value '[0.28494624 0.28494624 0.28494624 ... 0.25806452 0.25806452 0.25806452]' for dtype 'int64'`. Код и `expect` до сдачи сохранены в input; полный текст реакции и SHA кода — в [JSON](coordination-initial.json).
- `05-project/compare`: [student/raw/05-project-01-input.jsonl:9](student/raw/05-project-01-input.jsonl) → [student/raw/05-project-01-feedback.jsonl:9](student/raw/05-project-01-feedback.jsonl). `TypeError: Cannot clone object '<__main__.TrendBoost object at 0xb209338>' (type <class '__main__.TrendBoost'>): it does not seem to be a scikit-learn estimator as it does not implement a 'get_params' method.`. Код и `expect` до сдачи сохранены в input; полный текст реакции и SHA кода — в [JSON](coordination-initial.json).

Parsons p-gd и p-batch — отказ посредника сопоставить эквивалентные строки/отступы с буквальными UI-блоками, не отрицательный вердикт знания. Последующие буквальные сборки приняты. bisect — ученик пропустил доступную grad, исправил по traceback. split — дробная вероятность присвоена int64, затем приведена к float. compare — sklearn.clone вызван для пользовательского TrendBoost без get_params, повтор через deepcopy принят. Рецензент не объявляет эти пользовательские ошибки критическими дефектами курса; для compare согласована локальная помощь с созданием нового экземпляра. [По-ID решения](fixes/review.md) · [Собственные объяснения ученика](student/findings.md).

### Помощь и ограничения Cognitive Walkthrough

Ученик декларирует 0 подсказок и отсутствие открытия чужих решений/проверок; декларация сохранена, но чтение подсказок независимо не телеметрируется. Теория, заготовка, предыдущие собственные знания и редактура Parsons до отправки остаются доступной опорой. Q1–Q3 представлены непустым `expect` во всех 93 реальных input, Q4 — исходным feedback и [progress](student/progress.md). Многие Q1/Q2 шаблонные; текстовая передача пачками и последовательность файлов не доказывают точное время чтения и рефлексии. [Открытый перенос до вариантов](student/open-transfer-before-options.md) сохранён отдельно. Это агентное прохождение в текстовом пакете с мостом Chromium и native, без визуальной оценки интерфейса и без измерения человеческого темпа.

## Независимые программы и решения

У 36 программ совпали исходный код, SHA и зафиксированный [expected до запуска](check-evidence/expected-before-execution.json). В [CPython](check-evidence/before-native.jsonl) и [Pyodide](check-evidence/before-pyodide.jsonl) по 34/36 ожидаемых исходов, одинаковые вердикты, ложные зачёты C30/C31. Группы: original 4/4 соответствий (0 зачётов), migration 4/4 (2 зачёта), historical-additional 12/12 (6 зачётов), new 14/16 (9 зачётов). Исторические 20 программ не превращаются в новые 16.

У [18 программ рецензента](fixes/reviewer/before-programs.json) SHA кода совпал с результатами [CPython](fixes/reviewer/before-native.json) и [Pyodide](fixes/reviewer/before-pyodide.json); вердикты попарно одинаковы. На исходном контракте 11/17 ожидаемых результатов, шесть ложных зачётов: R04/R05 координаты графика, R07/R08 длина последовательностей, R10 epsilon Adam и R12 обучение до таймера с пустым fit. R18 решает **предлагаемый новый период EDA**; исходный отказ согласован со старым условием и не считается ошибочным отказом курса. Для итоговой сверки та же программа должна быть принята после явной миграции условия.

Примеры исходного stdout: R01 `bike: 11`, доля `0.0`, q90 `10.36`; R02 `bike: 10`, доля `1.0`. У R06 исходные списки const `[61.027, 60.955, 62.887, 60.48, 60.332]`, decay `[60.068, 60.07, 60.064, 60.048, 60.044]`. Точное содержимое всех программ и ответы системы лежат по приведённым ссылкам.

В [старом реестре](technical/prior-findings.json) 15 уникальных ID: S10-01–05, E10-01–05, M10-01–05. Для каждого найдена отдельная строка решения в [review](fixes/review.md), полная строка скопирована без переоценки в JSON. Новых ссылочных ID 36: 7 X + 2 C + 7 M + 6 T + 3 B + 10 ST + REV10-01. Они включают отвергнутые дефекты и сильные стороны; это **не 36 подтверждённых проблем**. Нужна последующая сверка исправления с каждым вердиктом, включая объединённые причины.

## Native и независимая передача

В [native-extra.ipynb](student/native/native-extra.ipynb) исполнены 10/10 code cells, error outputs нет; CSV содержат [5 публичных результатов](student/native/public-repeat.csv) и [8 упражнений](student/native/exercises.csv). Два ранних блокнота содержат ModuleNotFoundError lightgbm, окончательный — собственные outputs после выбора ядра. Сохранён [первый дизайн](student/native/native-extra-first-design.ipynb) с другими seed/patience/cap; он не входит в контролируемое сравнение. Финальный общий контроль 0/100/3000 заявлен в [README](student/native/README.md). Абсолютные predict публичной таблицы (лучший из пяти) и упражнения (один вызов) имеют разные процедуры. Ошибки среды и экспериментального дизайна не преобразованы в дефекты курса.

Получатель заморозил 16 файлов [first-inputs](fixes/recipient-evidence/first-inputs-manifest.json); все текущие SHA независимо совпали. В [verification](fixes/recipient-evidence/verification.json) семь exit_code=0. **Первым действием** была загрузка сохранённой модели без refit: 1104 строки, 1104 ключа, max difference=0, SHA model до/после одинаков. Затем проверены октябрь–декабрь (552), одна строка, перестановка, неизменность saved-model при будущей мутации, чистое обучение блокнота и refit при будущей мутации. Новый период использует июльскую модель; выпуск новой октябрьской модели CLI не предоставляет — это ограничение сохраняется. Отдельный stdlib JOIN plan/public CSV повторил RMSE 8.672295629326 тыс. ₽, MAE 6.335017907405 тыс. ₽, bias actual−prediction -0.537929554353 тыс. ₽ на кофейню-день. Это проверка сохранённых результатов, не повторная десериализация модели координатором. [Отчёт получателя](fixes/recipient.md).

## Что требуется после правок

1. Зафиксировать финальные SHA затронутых content/site/notebook/data и свежий export; отделить исправленную версию от c637497.
2. Сверить after 36 программ на обеих поверхностях по тем же literal code/SHA и заранее объявленным expected; отдельно показать исходные 4, миграционные 4, дополнительные 12 и новые 16.
3. Сверить after 18 программ рецензента на обеих поверхностях; все шесть исходных ложных зачётов должны стать отказами, допустимые альтернативы сохраниться, R18 учитываться по новому периоду. Проверить REV10-01 реальным fit внутри таймера без порога длительности.
4. Проверить новые первые попытки ученика в изменённых заданиях, полный payload input/feedback, использованную помощь, собственный открытый перенос и видимость поручения до сдачи. Старые 88 успешных сдач не заменяют ретест новой редакции.
5. Сверить проект и native с финальным опубликованным пакетом и 7 проверками получателя; сохранить отдельность frozen-first-inputs, повторного обучения и обновлённого выпуска.
6. По каждому из 15 прежних и 36 новых ID указать итоговое решение/ссылку; собрать итог главы с пятью методическими оценками и конкретными редактурами. До этой сверки принятие главы не объявлять.

<!-- final-coordination -->

## Финальная сверка публикации и повторов

Финальный полный экспорт `8ff17166358ce5ac586236711acfee23d2292cf822448bbaddd6034795eb310a`, глава `c4f346cc0c34869d8aa99d80da7123cfeeda47ee32b8883dfd249b764723d05e`. Проверены SHA 54 файлов выпуска; исходный coordination-initial.json сохранён без изменения. Собственные запуски ограничены чтением/JSON/CSV/SHA. [Исполнитель](coordination-final.py) · [Результат](coordination-final.json) · [По-ID покрытие](coverage.json).

Raw исходного ученика снова точно сверены по всем полям, включая visible_prompt и кратность. Повтор: 34 событий, 34 graded, 34 уникальных целей, последний зачёт 34; multiset raw и retest-attempts совпал точно. Целей по реестру 34; отсутствуют [], лишние []. Это повтор знакомого материала.

| Исходный input повтора | Feedback | Строк |
|---|---|---:|
| [01-gradient-01-input.jsonl](fixes/student/retest/raw/01-gradient-01-input.jsonl) | [01-gradient-01-feedback.jsonl](fixes/student/retest/raw/01-gradient-01-feedback.jsonl) | 1 |
| [01b-numeric-01-input.jsonl](fixes/student/retest/raw/01b-numeric-01-input.jsonl) | [01b-numeric-01-feedback.jsonl](fixes/student/retest/raw/01b-numeric-01-feedback.jsonl) | 3 |
| [02-gd-many-01-input.jsonl](fixes/student/retest/raw/02-gd-many-01-input.jsonl) | [02-gd-many-01-feedback.jsonl](fixes/student/retest/raw/02-gd-many-01-feedback.jsonl) | 1 |
| [02b-optimizers-01-input.jsonl](fixes/student/retest/raw/02b-optimizers-01-input.jsonl) | [02b-optimizers-01-feedback.jsonl](fixes/student/retest/raw/02b-optimizers-01-feedback.jsonl) | 2 |
| [04-tuning-01-input.jsonl](fixes/student/retest/raw/04-tuning-01-input.jsonl) | [04-tuning-01-feedback.jsonl](fixes/student/retest/raw/04-tuning-01-feedback.jsonl) | 3 |
| [05-project-01-input.jsonl](fixes/student/retest/raw/05-project-01-input.jsonl) | [05-project-01-feedback.jsonl](fixes/student/retest/raw/05-project-01-feedback.jsonl) | 8 |
| [06-libraries-01-input.jsonl](fixes/student/retest/raw/06-libraries-01-input.jsonl) | [06-libraries-01-feedback.jsonl](fixes/student/retest/raw/06-libraries-01-feedback.jsonl) | 2 |
| [test-01-input.jsonl](fixes/student/retest/raw/test-01-input.jsonl) | [test-01-feedback.jsonl](fixes/student/retest/raw/test-01-feedback.jsonl) | 14 |

39/39 критика в каждой среде = 36 буквальных исходных + C36M + два нулевых интервала; отдельные четыре closure-программы дают 4/4. C36 отвергнут после явной смены периода, его апрельская миграция принята. До финальных closure у 55 остальных карточек неизменны setup/starter/check/solution; изменены только два check для 400 точек и grid. Независимый рецензент: 19/19 в каждой среде, 9 зачётов и 10 отказов.

Рассмотрены 54 ID, включая исторически закрытое, повторные формулировки одной причины, сильные стороны и отклонённые дефекты. Полный ledger перенесён в coverage; число 54 не является числом независимых ошибок. Методист после ретеста: 4,40/5 (5/4/4/4/5), исходно 3,60.

Новая передача: проверены SHA 31 файлов second-inputs; 10 сравнений по ключам и 11 команд exit0. Первый saved без истории имеет fit_calls=0, независимо выбранный выпуск 1 октября использует 3834 строки до 30 сентября; 552 результата и все варианты запроса/истории совпали. Это CLI-приёмка; Jupyter повторно не запускался. [Квитанция](fixes/recipient-evidence/verification2.json).

Ожидания завершения: нет. Глава принята; внешний методический пилот сохраняется отдельно.
