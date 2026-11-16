# Точка продолжения критика автопроверок

Версия курса `b3291d4238a7579a8ceb13bded7c027a2d90a2a0`. Работа ограничена главой 12. Source/site/notebooks/data не менялись. Before132 завершён в CPython и Pyodide, оба exit0, 108/132 нормативных совпадений и одинаковые24 расхождения; все50 baseline прошли. CPU освобождён и передан root. Новые CPU-запуски только после отдельного разрешения координатора. Полный отчёт: ../checks.md.

## Что готово

- `pre-check-promises.md`: учебные обещания и единицы/ключи всех 50 task записаны по публичным материалам до чтения check/setup/solution.
- `visible-contracts.json`: полные публичные условия и заготовки, 50 ID.
- `before-tasks.json`: 50 baseline task с полными setup/check/solution.
- `programs.jsonl`: 132 полные программы с замороженным нормативным expected, SHA, группой; все 50 task покрыты авторской программой и отрицательным случаем.
- `expected-before-execution.json`, `frozen.sha256`: ожидания и отпечатки до исполнения. Текущий programs SHA `00fcb5be8b1f751b85e03ac487f35a7e65e7a43cc771105fed0237e92f481f77`; expectations SHA `7e16b3c908e0a45085f70f4148b71ad5ad46b8f6820a8752e5bc6627d9649c88`.
- `before-source-hashes.json`: исходники главы, harness, реальные файлы Pyodide, прежние драйверы и результаты. `data-baseline/app_orders.csv` SHA `53c3351867d2c2bbf8decdd70daba5aa7eea2b5010154c52a115e29810666235`.
- `historical/`: полные буквальные файлы прежних драйверов. Прежняя 35-пакетная и текущая 69-пакетная регрессия содержат ровно две программы главы12; это буквальные C001/C002 со старыми SHA `f3760e15396e4b2d0348429cb1540bb84adc0d3b4b7f6818136cddb63dcd3cb7` и `6fe07ad3eedf34d9a479f1e3ca0394f96958b80403e50b884ef1e0a687f7a9d0`. Для них контракт не менялся, миграций нет.
- C003–C006 повторяют выражения `c.probe` из исторического acceptance-драйвера **на замороженном текущем авторском решении**. Это не выдаётся за сохранённый исторический полный код ученика. C132 изолирует оставшиеся исторические assertions доступности последних четырёх меток и 24 будущих строк; его адаптация драйвера явно записана в строке. Сам исторический файл сохранён буквально и захеширован.
- `transfer_staffing.py`: отдельный stdlib перенос мощности 4/6/8 и цены нехватки 300/1200; не скрытое требование исходной карточки (там мощность6).

## Команды после разрешения CPU

Из корня репозитория последовательно, threads=1:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /private/tmp/ku-audit/nb-env/bin/python docs/reaudit-2026-11-16/ch12/check-evidence/run_native.py before
```

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 node docs/reaudit-2026-11-16/ch12/check-evidence/run_pyodide.mjs before
```

Оба раннера записывают полный код, feedback, stdout, execution_error_type и failure_stage; средовая/ученическая ошибка исполнения не считается автоматически дефектом check. Для четырёх Parsons с group=parsons-error ожидается ошибка исполнения из-за недопустимой перестановки строк. Сверять ожидаемый отказ с `passed=False`, но трактовать `ok=False` отдельно. Для доступности финала дополнительно смотреть transfer_oracle.

## Что проверить после before

1. Расхождения expected/passed в двух средах; отсеять случайные неразличающие мутации и ошибки в самих probe. Исходные программы и expected не перезаписывать; коррекции интерпретации вести отдельным JSON/MD.
2. Статические подозрения (пока не findings):
   - `leak-test`: публично +1000 только в t; check и авторское решение портят весь хвост разными знаками/квадратичными добавками.
   - `grid`: публично TimeSeriesSplit(3), check требует gap>=28. Нужно исправить публичную спецификацию отдельно от усиления check.
   - `month-folds`: названы май/июнь/июль, перечислены ключи06/07/08; check принимает05/06/07.
   - `load` не сверяет сами orders; `growth` не проверяет trend28; `diff` не проверяет d1/d7; `make-features` проверяет лишь первую строку функции и не проверяет сдаваемый df целиком.
   - `months` сравнивает `.values`, игнорирует месячные ключи, и `zip` допускает пустые векторы.
   - `daily` игнорирует ключи week_days, но отвергает перестановку корректных именованных рядов; некоторые другие именованные Series/DataFrame требуют порядок без публичной причины.
   - `acf-plot` проверяет число столбцов и label, но не высоты.
   - `noshuffle` — первоначальное подозрение снято: test_start проверяется, C064 отклонён.
   - `metrics` не проверяет WAPE на нулевом факте, хотя отдельная карточка wape делает это.
3. После фактических результатов написать `checks.md`, находки `CH12-CHECK-01…`, proposal.patch/private proposal-tasks. Source/site менять только после отдельного разрешения root.
4. After прогонять **те же codes и expected**. Скопировать `programs.jsonl` в `after-programs.jsonl` без изменений; after-tasks получить из согласованной редакции. Изменённые публичные требования leak-test/grid/month-folds явно перечислить как миграции контракта (старые позитивы не переименовывать в ошибочные решения).
5. Сверить stdout реальных before/after native/Pyodide, составить общий coverage50 и результат исторических двух. Не читать и не передавать студенту отчёты/цифры других ролей.

## Обновление после before и согласования миграций

Подготовлен source-private `proposal.patch` (20task, 465строк), `proposal-tasks.json`, `propose_checks.py`. Source/site/data не менялись. Синтаксис50task/4полей и дополнений прошёл AST; git apply --check прошёл. Проза/условия/hints/explain/рисунки принадлежат эксперту, согласуйте его patch перед source-редакцией.

Новый проектный контракт: baseline740 до31.07 20:00; select fit_mask до30.06 20:00 и valid_score740 до31.07 20:00; grid толькоCV/gap28 без августа (setup s<Aug1); final один раз оценивает август и считает rmse_base именно по августу. Promo: полный публичный календарь5дат, make_promo(index) Series0/1 с часовыми ключами, df["promo"] сохраняется; будущие y не требуются.

Дополнительно **до исполнения** заморожены supplement-programs.jsonl (S001/S002: различающий C066oracle) и migration-programs.jsonl (M001–M014: адаптированные позитивы/негативы/перестановки helper). expected-phase.json хранит отдельно expected_original и expected_current_contract для132; исходный файл expectations не меняется. Check-evidence/supplement-frozen.sha256 связывает эти файлы с proposal-tasks. Новые программы ещё не выполнены.

После root-approval на патчи и CPU:
1. Сохранить after-tasks.json из согласованных четырёх полей (proposal либо свежий build-export после применения).
2. Скопировать programs.jsonl→after-programs.jsonl побайтно.
3. Последовательно `run_native.py before --bundle supplement`, `run_pyodide.mjs before supplement`; затем after132 и after migrations/supplement. Native bundle: `run_native.py after --bundle migration`; Pyodide: `run_pyodide.mjs after migration`.
4. Общее before132 не повторять без причины. Фазовые ожидания оценивать отдельно от буквальных frozen expected; C061/C095/C097/C099/C120/C121/C122 явно мигрируют.
5. Для S002 смотреть не только основной grade, но transfer_oracle.check.passed=False; это докажет, что прошедшая before программа нарушает публичный max/min контракт. S001oracle должен пройти.
6. По фактическому after закрыть/скорректировать CH12-CHECK-01…10 в ../checks.md; при любых средовых/программных ошибках сохранить trace и не переписывать frozen программы задним числом.


## Окончательная приёмка

Actualafter50task взяты из W/revised.json, SHA6c79570eaa74382f5a5e46ed51bd426748039c7a4b3d993f57add467e8071ef0. Все50×4поля сопоставлены с proposal:18 отличий только концевые переводы строк. Реальных изменённыхchecks19, codecards20, codefields29/200.

Before supplement2 и after132/supplement2/migration14 выполнены последовательно в CPython и Pyodide. After132:125/132originalexpected,132/132currentcontract; after supplement2:2/2; aftermigration14:14/14. Семь intentional migrations документированы expected-phase.json. C066 подтверждён независимым oracle и отклоняется actualaftercheck; всеCH12-CHECK-01…10 закрыты в ../checks.md. Неизменность исходных132codes/expected и CSV/runtime проверена finalize_checks.py; итоговые SHA в actual-acceptance-sha256.json. CPUFREE передан root. Новых ML/NumPy/Node запусков без разрешения root не требуется. Source сам агент не менял.
