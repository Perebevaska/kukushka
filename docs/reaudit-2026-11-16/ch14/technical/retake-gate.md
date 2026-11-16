# Gate подготовки retake главы14

Генератор `prepare-retest.py` создан до завершения редакции; без параметров он только сообщает HOLD и ничего не генерирует. Не запускать подготовку до SOURCE-READY обоих редакторов и rootbuild/export. Root после готовности вызывает:

```sh
python3 docs/reaudit-2026-11-16/ch14/technical/prepare-retest.py --prepare --source-ready --export /private/tmp/kuch14round/final.json
```

Он сверяет actualfinalс frozenW/original по каждому tasksection с кратностью hint; выбирает все изменённые задачи, carryingtasks изменённой теории, затронутые embedded/predict и все15final. Проверяет совпадение source/exportID и checkdiff, буквальные codeполя экспортной версии. Создаёт отдельный publicstudent-retest и privatekeys/hints/reference. Отдельно проверяет, что парковка находится в обычной theoryдо первогоtask и передtask-dayвсобранномHTML; её нельзя извлекать из hiddenexplain и выдавать за исходно публичную. Разборыdetailsудалены. Брифписьма должен находиться вtheory. Optionalлокальныйопыт послеalertsможетоставаться вегоexplain:выделяется толькоhumanproseдля чтения после сдачиalerts, без авторских программ и решений.

После prepare root отдельно рендерит19PNG `node /private/tmp/kuch14round/public-figures-retest.cjs`, затем:

```sh
python3 docs/reaudit-2026-11-16/ch14/technical/prepare-retest.py --finalize --source-ready --export /private/tmp/kuch14round/final.json
```

Finalgate повторно сверяетsource/export/HTMLSHA,PNG и59+10+14SHAсобственного ученика. Только затем rootможетвыдатьпакет иCPUокно. Скрипт невыдаётпакет и не запускаетbrowser/ML. Новыйbridgeиспользуетjobs-retest иstop-retest, пишет aggregate/imagesвfixes/student/retest, initialкаталог нерасширяет. Selectorстрогоtask-uiCodeMirror+readback.

Вpublicпереходят лишь собственныеinitial59иholdout10+14файлыученика, егоknowledge, код и прежниеошибки. Чужиевыводы и privatekeys не копируются. Дляопискиholdoutпросимсамостоятельносверить текстовыечислителисJSON/CSV; правильное число заранее невкладывается.

Отдельный scopedредакторскийаспект E14-07, назначенный root: ранняя фраза04b«маленькуюголовупочтиневозможнопереобучить» и гарантия«огромныхградиентов» должны быть заменены условными проверяемыми формулировками. Это прозовая правка доafterприёмки; отдельная программа/оценка пока не заявлены. Послеготовности нужна сверкаэкспертаирецензента.
