# Глава 6. Критик автопроверок

16 ноября 2026. Исходный SHA `5c4c2efe1f75243e763b5cd583952ab5d49ccf45`. Роль — Sol high. Прочитаны `course-audit.md`, `course-reaudit-plan.md`, исходные материалы главы, прежние expert/student/review/methodist/report, приёмки и все 14 исторических ID. Работа этой роли — исполнимые контракты, без самостоятельного прохождения за ученика и без вывода о темпе человека.

Сверены **98 задач в 11 тематических уроках**; введение не содержит исполнимой задачи, итоговый тест относится к отдельной роли. Полный реестр с отпечатками всех starter/setup/solution/check — [contract-coverage.json](check-evidence/contract-coverage.json). Для каждого урока взята новая пара «другой правильный способ / правдоподобная ошибка». Это отдельный знаменатель от штатных 178 task/example/predict и от самостоятельных сдач ученика.

В каждой среде выполнено **53 адресные пробы: 27 положительных и 26 отрицательных**. У исправленной редакции **53/53** ожидаемых вердиктов. В исходной редакции 19 расхождений с целевыми критериями: **13 по неизменённому исходному контракту**, три по ошибочной процедуре подбора, два по переносу бюджета на новый пул и один по встроенной проверке singleton. Это не 19 независимых дефектов. В пяти случаях изменялось само условие, что отмечено ниже.

[Фиксированный пакет рецензенту](check-evidence/review-brief.md) · [Исходные коды проб](check-evidence/probes-original.json) · [Новая редакция кодов](check-evidence/probes-revised.json). В JSONL сохраняются ожидаемый вердикт, полный сданный код, исходная реплика harness и фактический вердикт. Диагностика моделей, меток и ID сохранена полностью, а не сведена к accuracy: [CPython](check-evidence/observations-native.json), [Pyodide](check-evidence/observations-pyodide.json).

## Новые наблюдения и узкие исправления

| ID / приоритет | Наблюдение до исправления | Изменение и критерий приёмки |
|---|---|---|
| T06-01 · P1 · `xy`, `split`, `three-parts` | C02/C05/C26: переставленные или инвертированные метки при исходных ID получают зачёт. Сумма класса/индексы частей не определяют правильную целевую переменную. | Сверяются значения X/y по исходному ключу, не только длина/число True. C01/C04/C25 сохраняют другой корректный способ и согласованный порядок признаков. Числовые равные значения не отвергаются только из-за dtype. |
| T06-02 · P1 · `first-tree`, `first-forest` | C03/C16: после расчёта отчётной метрики переданный объект переобучен на нулях и принят. CPython: дерево сообщает 0,798 при реальных 0,76046; лес — 0,898 при реальных 0,76790. | Проверка вызывает реальный predict переданного объекта и сверяет вектор с обучением по настоящим меткам; метрика пересчитывается после последнего fit. |
| T06-03 · P1 · `shop-rate` | C09: правильный эквивалентный inline-фильтр через `d.loc[...]` отвергнут, потому что скрытая проба подменяла переменную с именем `ok`, а код ученика её при split не использовал. | Входом служит настоящий CSV с той же видимой схемой. Replay не предполагает имён промежуточных переменных. C08/C09, в том числе join вместо map, получают зачёт. Файл восстанавливается в finally. |
| T06-04 · P1/P2 · `shop-rate` | C11: y_train переставлен при сохранённых ID, проверка принимает старый правильный mapping. C13 сам по себе на шести крупных точках ничего не удаляет: это не неверные значения на исходном файле. Однако программа теряет реальный singleton в C40. | Явно сверяются обе y-Series по ID. Встроенная проба создаёт один train-заказ кофейни SINGLE-TRAIN (индекс 963) и неизвестную test-точку (1590). Проверяются все строки, ставки, метки и mapping; train singleton получает собственную метку согласно открытому учебному контракту, test unknown — среднее только train. C39/C41 — реальные таблицы; C40/C42 — содержательные отказы. OOF не подставлен вместо задания. |
| T06-05 · P1 · `calib` | C19: перестановка целых строк таблицы отвергнута. C20: перестановка только подписей интервалов при старых числах принята. | Ключ — интервал вероятности. После проверки множества уникальных интервалов строки выравниваются по ним. Одинаковая перестановка ключа и статистик допустима, подпись чужой группы — нет. |
| T06-06 · P1 · `final`, `top` | C34/C50: `prepare` разрешает согласованный порядок колонок, но корректный RF с алфавитной схемой в дальнейшем отвергнут. RF с одним seed и другим порядком признаков может выдать другой законный вектор: native accuracy 0,895 вместо 0,898, Pyodide 0,897 вместо 0,900. | Контрольный RF обучается в том же порядке feature_names_in_, при неизменном множестве допустимых признаков. Сверяются реальные векторы предсказаний/вероятностей. Корректная альтернативная схема проходит оба шага. |
| T06-07 · P1 · `top` | C36: winner переобучен на test перед расчётом всех согласованных списков и получает зачёт. Старый final проверяет такую подмену, следующий top — нет. | Явный контракт «та же модель шага 8, train-only». На всех исторических и рабочих строках вероятности переданного объекта сравниваются с train-only RF в согласованной схеме. Согласованности скаляров и своих списков недостаточно. |
| T06-08 · P2 · `speed-table` | C29: реальные fit/predict выполнены, но затем длительности заменены константами; зачёт сохраняется. Также старая проверка требует заранее известного порядка моделей по скорости. | Первый запуск сохраняет настоящие измерения. Повторный запуск реально выполняет fit/predict с событийным секундомером и проверяет происхождение разностей. Подстановка чисел отвергнута, авторский и другой порядок обучения приняты (C43/C44). Утверждение, что лес обязан быть медленнее дерева при любых замерах, убрано. Методы и часы восстанавливаются в finally. |
| T06-09 · P2 · `leaf-size`, `threshold`, regression `depth` | C45–47 показывают зависимость выбора от меток test. Это соответствует старому видимому требованию; ошибка находится в самой процедуре, а не в работе ученика. Исторический E06-03 закрыт лишь частично: проект исправлен, threshold оставался прежним; выбор по test встречается и в двух других карточках. | Условия, starter, solution, check и hints согласованы: сначала final test 25 %/seed42, затем validation 25 % остатка/seed43. Выбор делается только по validation. В leaf-size новое имя validation_by_leaf. При изменении final y_test все три правильные программы сохраняют зачёт. Качество подобранного порога на validation не объявляется независимой итоговой оценкой. Нужен ретест изменённых условий учеником. |
| T06-10 · P2 · `top`, `quiet` | Поля current_risk/current_ids были спрятаны в explain предыдущего шага. В quiet разрешение ничьей задано только неявной сортировкой числового индекса. На 40 новых рабочих строках правильный список из четырёх отвергался проверкой, ждущей 240. C51–52 — перенос на новые данные, не отказ по прежнему файлу 2400 строк. | Все поля рабочего результата перечислены в условии top. Лимит — int(len(current)*0.1); исторический и рабочий пул различены. В quiet условие, hint, solution и check одинаково разрешают ничьи по guest_id. C51 даёт 4 ID; на 40 равных рисках C52 принимает WORK-000…003, C53 отвергает первые четыре входные строки. |

## Покрытие уроков новыми парами

| Урок | Задач | Другой корректный способ | Новая содержательная ошибка |
|---|---:|---|---|
| 01-what-is-ml | 11 | C01: loc и отдельная Series меток | C02: перевёрнутые значения y при прежних ID; C03: подмена обученной модели |
| 02-split | 10 | C04: split индексов и loc | C05: независимая перестановка y_train |
| 03-tree | 9 | C06: выбор вероятности по classes_ | C07: перевёрнутые прогнозы при старом X_test |
| 04-categorical | 10 | C08/C09: join, другой фильтр, порядок строк | C11: потеря привязки метки; C40: реальный потерянный singleton |
| 05-forest | 10 | C14: stack/sum вместо mean списка | C15: неверный порядок вероятностей; C16: stale metric другой модели |
| 06-logistic | 6 | C17: индекс класса из classes_ | C18: перестановка вероятностей без доставок |
| 06b-probabilities | 6 | C19: перестановка целых строк cal | C20: перестановка только меток интервалов |
| 07-regression | 10 | C21/C23: перестановка целых строк/пар | C22/C24: независимая перестановка только pred или fact |
| 08-validation | 10 | C25: другой согласованный порядок признаков | C26: инверсия меток validation при прежних ID |
| 08b-groups-speed | 6 | C27: intersection; C44: другой честный порядок замера | C28: union вместо intersection; C29: выдуманные секунды |
| 09-project | 10 | C30/C32/C34/C35/C50: схема, predict, сортировка | C31: целевой ответ вместо признака; C33/C36: test fit; C37/38: неверная связь вероятностей и IDs |

## Все прежние замечания

| Исторический ID | Состояние после проверки |
|---|---|
| S06-01 | Контроль depth-curve проходит; изменение final y_test не влияет на train/validation/best_depth (A06/A07). Предупреждение о test уже реализовано до этого прохода. |
| S06-02 | NumPy присутствует в starter threshold. Новый перевод threshold на validation сохраняет импорт и сетку 0.10…0.85. |
| S06-03 | C48: все 1800 ID демонстрации утечки исключают финальные 600; внутри демонстрации свои train/valid. Пересечение пусто. Это самостоятельная проверка, не вывод из scalar accuracy. |
| E06-01 | Раздельные historical/current файлы и даты существуют. Их предметную достоверность и новый отдельный пул проверяет expert; C39/C41/C51 проверяют применимость к новому объекту и ключам. Baseline этого пакета сохранён до смены current-ID на G-30001…32400. Полный финальный датасет — отдельный прогон координатора. |
| E06-02 | Старые мутации prepare/final/top отвергаются (A01–A04); C30 сохраняет другой порядок колонок prepare. Найденный остаток final/top C34/C36/C50 исправлен, закрытие возможно после независимой рецензии. |
| E06-03 | Проектная демонстрация отделена от final (C48). Остаток threshold подтверждён; процедура исправлена вместе с leaf-size/regression-depth. На C45–47 изменённое условие требует нового прохождения, старый код нельзя объявлять ошибкой ученика. |
| E06-04 | Граница train/test сохраняется. Среднее train включает свою обучающую метку по явно объявленной демонстрации; C49 обоснованно не принимает leave-one-out как эквивалент. Это не доказательство пригодности учебного кодировщика в работе. Unknown/singleton/ID проверены реальными строками. |
| E06-05 | C23 принимает правильные переставленные пары scatter, C24 отвергает независимый разворот fact; A05 и C21/C22 подтверждают привязку residuals по ID. |
| E06-06 | В top сравниваются те же 60 мест модели и давности, в рабочем пуле лимит пересчитывается. C51/C52 добавляют ранее не выполненный перенос 40→4. Выбор бизнес-критерия и вывод о пользе бонуса относятся к expert/methodist; технический зачёт не доказывает causal effect. |
| M06-01 | Переданные model/forest и их метрики проверяются; C36 нашёл и закрыл обход в следующем шаге top. Полные векторы сохранены. |
| M06-02 | Равный бюджет сохранён; новый 40→4 и ничьи предъявлены реальными очередями. В quiet порядок исправлен на guest_id. |
| M06-03 | Среднее и std остаются разными величинами; кандидаты используют общие фолды. Проверка final теперь сохраняет разрешённый порядок признаков. Выбор и интерпретацию CV подтверждает предметный expert. |
| M06-04 | A08 учитывает все пять вероятностей [0,.25,.5,.75,1]. Дополнительно T06-05 закрывает потерю соответствия между интервалом и частотами. Проверку zero-edge не выдаём за контроль всех остальных аспектов калибровки. |
| M06-05 | Учебная train-accuracy обозначена в уроке; T06-02 теперь требует её от реально переданного объекта. Процедуры подбора согласованы с ранее исправленным depth-curve. |

## Штатный контроль и среды

`tools/checks/ch06_acceptance.py` прошёл: семь адресных программ и контроль калибровочных границ/дат/схемы. Неизменённый stdout — [acceptance-native.txt](check-evidence/acceptance-native.txt). Те же A01–A08 исполнены в обеих средах: [native](check-evidence/native-acceptance.jsonl), [Pyodide](check-evidence/pyodide-acceptance.jsonl). Это не новый запуск всех 69 старых программ курса.

- CPython 3.12.14; NumPy 2.4.6, pandas 3.0.6, sklearn 1.8.0; `/private/tmp/ku-audit/nb-env/bin/python`, зависимости из `.venv/lib/python3.12/site-packages` через PYTHONPATH.
- Node и точные версии Pyodide/Python/пакетов записаны в первой строке `pyodide-revised.jsonl`. Pyodide 314.0.7 / Python 3.14.2; sklearn 1.8.0, pandas 3.0.2. Числа RF между средами отличаются, поэтому проверка строит контрольную модель в той же среде и схеме, а не требует CPython-скаляр в браузере.

Сайт этой ролью не собирался, Chrome не открывался. Экспорт получен парсером content; `catalog-revised.json` содержит 178 записей. Полный штатный прогон, опубликованные блокноты, финальный новый рабочий CSV и ретест ученика — отдельные свидетельства координатора. Пробы ниже относятся к замороженному пакету и не заменяют их.

## Ведомость всех 53 проб

`+` — зачёт, `−` — отказ. Одинаковые вердикты получены CPython и Pyodide; исходные реплики не редактировались. В исходной колонке C45–47 относятся к старому требованию выбора по test; C51–52 — к переносу на новый размер пула, C13 — к встроенному singleton-кейсу.

| Проба | Карточка | Вариант | Целевой expected | Исходный observed | После |
|---|---|---|---|---|---|
| C01 | `01-what-is-ml/xy` | alternate explicit loc and copied labels | + | + | + |
| C02 | `01-what-is-ml/xy` | labels reversed, original row IDs retained | − | + | − |
| C03 | `01-what-is-ml/first-tree` | fitted model overwritten by fit on zeros; stale train metric | − | + | − |
| C04 | `02-split/split` | alternate split per matching index | + | + | + |
| C05 | `02-split/split` | labels shifted under retained split row IDs | − | + | − |
| C06 | `03-tree/proba` | alternate positive-class lookup and list | + | + | + |
| C07 | `03-tree/proba` | probabilities reversed independently of test rows | − | − | − |
| C08 | `04-categorical/shop-rate` | join instead of map; complete row sorting | + | + | + |
| C09 | `04-categorical/shop-rate` | equivalent filter inline instead of variable ok | + | − | + |
| C10 | `04-categorical/shop-rate` | shop labels sorted separately from encoded values | − | − | − |
| C11 | `04-categorical/shop-rate` | training labels shifted but old shop mapping retained | − | + | − |
| C12 | `04-categorical/shop-rate` | unknown test shop falls back to test mean | − | − | − |
| C13 | `04-categorical/shop-rate` | silently drop singleton training groups | − | + | − |
| C14 | `05-forest/avg-proba` | alternate stack then axis 0 average | + | + | + |
| C15 | `05-forest/avg-proba` | independent reordering of averaged probabilities | − | − | − |
| C16 | `05-forest/first-forest` | forest refit on zeros while preserving reported accuracy | − | + | − |
| C17 | `06-logistic/proba` | alternate class-column lookup | + | + | + |
| C18 | `06-logistic/proba` | correct histogram with shuffled order IDs | − | − | − |
| C19 | `06b-probabilities/calib` | alternate correctly reordered group rows | + | − | + |
| C20 | `06b-probabilities/calib` | group labels reversed independently of numeric statistics | − | + | − |
| C21 | `07-regression/residuals` | alternate full row order | + | + | + |
| C22 | `07-regression/residuals` | only predictions reassigned under unchanged IDs | − | − | − |
| C23 | `07-regression/fact-pred` | alternate pair order on scatter | + | + | + |
| C24 | `07-regression/fact-pred` | fact independently reversed on scatter | − | − | − |
| C25 | `08-validation/three-parts` | alternate consistent column order | + | + | + |
| C26 | `08-validation/three-parts` | all valid labels flipped under original IDs | − | + | − |
| C27 | `08b-groups-speed/group-split` | alternate set operations for overlaps | + | + | + |
| C28 | `08b-groups-speed/group-split` | union instead of shared guest intersection | − | − | − |
| C29 | `08b-groups-speed/speed-table` | hardcoded durations after real measurements | − | + | − |
| C30 | `09-project/prepare` | alternate alphabetical feature order | + | + | + |
| C31 | `09-project/prepare` | target substituted for historical feature | − | − | − |
| C32 | `09-project/final` | alternate explicit accuracy from predict | + | + | + |
| C33 | `09-project/final` | refit on final test after reporting metric | − | − | − |
| C34 | `09-project/final` | same required RF and feature set with alphabetic column order | + | − | + |
| C35 | `09-project/top` | alternate nlargest after ID sort | + | + | + |
| C36 | `09-project/top` | winner accidentally refit on final test before producing consistent lists | − | + | − |
| C37 | `09-project/top` | current probabilities assigned under reversed guest IDs | − | − | − |
| C38 | `09-project/top` | wrong selected guest order | − | − | − |
| C39 | `04-categorical/shop-rate` | join correct on singleton train | + | + | + |
| C40 | `04-categorical/shop-rate` | actual singleton train removed incorrectly | − | − | − |
| C41 | `04-categorical/shop-rate` | join correct on singleton and unknown shop | + | + | + |
| C42 | `04-categorical/shop-rate` | unknown shop filled by test mean | − | − | − |
| C43 | `08b-groups-speed/speed-table` | author actual measured durations positive control | + | + | + |
| C44 | `08b-groups-speed/speed-table` | alternate model iteration order measured honestly | + | + | + |
| C45 | `03-tree/leaf-size` | final label perturbation must not affect chosen parameter | + | − | + |
| C46 | `06-logistic/threshold` | final label perturbation must not affect chosen parameter | + | − | + |
| C47 | `07-regression/depth` | final label perturbation must not affect chosen parameter | + | − | + |
| C48 | `09-project/leak` | demonstration diagnostic split excludes final IDs | + | + | + |
| C49 | `04-categorical/shop-rate` | leave-one-out is distinct from explicit training-mean contract | − | − | − |
| C50 | `09-project/top` | winner with consistent alphabetic input order | + | − | + |
| C51 | `09-project/top` | 40 candidate working pool, four exact IDs and scores | + | − | + |
| C52 | `09-project/top` | 40 tied predictions choose four smaller guest IDs | + | − | + |
| C53 | `09-project/top` | ties follow incoming row order instead of guest ID | − | − | − |

## Оставшиеся действия

Независимый рецензент должен воспроизвести исходные случаи и вынести решение по T06-01…10 отдельно от оценки минимальности правок. Для изменённых условий выбора и top требуется новая собственная сдача ученика. Новая рабочая когорта и предметные числа должны войти в общий окончательный export/прогон после синхронизации всех ролей. Никакая из этих внешних проверок не объявляется завершённой по одному прохождению 53 технических проб.
