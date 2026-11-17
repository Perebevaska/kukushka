# RCP15-R: ожидания независимого получателя до исполнения

Новая передача из `fixes/student/retest/own-project` принята в отдельные `/private/tmp/kuch15round/recipient-revised/incoming` и `working`. Исходная приёмка 53 файлов не изменена. Прочитаны только материалы этой передачи: README, requirements, паспорт и исходники её scorer/features, плюс соседняя заморозка `project-revision-freeze.json`.

Все 95 записей заморозки проверены по SHA-256 и совпали. В дереве источника дополнительно находились три `.pyc` в `src/__pycache__`, отсутствующие в заморозке: они не копировались в чистый пакет. Собственные `receipt-input-manifest.json` и `receipt-preflight.json` фиксируют именно 95 переданных файлов. База совпадает с паспортом по MD5 и SHA-256; golden содержит 20 уникальных ID и правильный порядок колонок. Это пока лёгкая проверка упаковки, не исполнение модели.

**CPU HOLD соблюдён:** NumPy/pandas/joblib/модель/ядро не импортировались и не запускались. После разрешения планируется пересчёт без обучения:

```sh
# cwd /private/tmp/kuch15round/recipient-revised/working
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export MPLCONFIGDIR=/private/tmp/kuch15round/recipient-revised/mplconfig
/private/tmp/ku-audit/nb-env/bin/python score.py --cutoff 2026-09-30
/private/tmp/ku-audit/nb-env/bin/python score.py --cutoff 2026-09-30 --call-limit 3 --out-dir reports/revision/rescore
/private/tmp/ku-audit/nb-env/bin/python /Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch15/recipient/revised/independent_receipt.py
```

Первый baseline берётся из исходного раздела README, лимит 3 — из нового раздела README с `--out-dir reports/revision/rescore`. Перед запуском прежние `reports/rescore` и `reports/revision/rescore` в рабочей копии будут перемещены в соответствующие `reference-rescore`, вход останется неизменным. Ожидается повторяемая загрузка frozen joblib, 20 контрольных вероятностей, совпадение schema/types/versions и результатов CSV/JSON. ID, города, состав/порядок, вероятность, деньги и полная сумма будут рассчитаны независимо заново из SQLite, без использования ожидаемых чисел прошлой приёмки.

Отдельная реализация получателя учитывает новый контракт: нулевой знаменатель revenue_trend даёт 0. Проверка готова сопоставить все 16 признаков всех текущих клиентов, исходные golden-входы с БД, а затем model probabilities на независимо восстановленных 20 строках. История источников/качество синтетической симуляции не заменяются успешным техническим пересчётом.

Используется существующая среда `/private/tmp/ku-audit/nb-env`; версии будут проверены фактически. Новая venv, установка зависимостей и Docker не заявляются. revision.py и notebook не запускаются этим получателем: они могут выполнять диагностический CV и относятся к отдельной проверке доработки.
