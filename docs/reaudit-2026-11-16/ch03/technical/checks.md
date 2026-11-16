# Техническая приёмка check/setup главы 3

Исходный экспорт содержит 207 записей, из них 93 task. Адресный набор — 58 содержательных программ и вариантов входа плюс 93 пустых ответа, всего 151. В after добавляется по одному текущему авторскому решению на каждый task — всего 244. Перед прогонами сайт не генерируется: `build.parse_lesson` и `build.export` читают только content/ch03 и раскрывают include-check.

Результаты: native 130/151 до, 244/244 после; bundled Pyodide 130/151 до, 244/244 после. Native: CPython 3.12.14, pandas 3.0.6. Pyodide: CPython 3.14.2, pandas 3.0.2. Обе среды исполняют поставляемый `site/assets/harness.py`. Файлы учебных данных копируются перед каждой пробой, нативная проба получает временную папку. По всем пробам совпали actual/expected и вердикты двух сред.

Из корня репозитория:

```sh
python3 docs/reaudit-2026-11-16/ch03/check-evidence/make_probes.py
PYTHONPATH=.venv/lib/python3.12/site-packages /private/tmp/ku-audit/nb-env/bin/python docs/reaudit-2026-11-16/ch03/check-evidence/run_native.py
node docs/reaudit-2026-11-16/ch03/check-evidence/run_probes.mjs
PYTHONPATH=.venv/lib/python3.12/site-packages /private/tmp/ku-audit/nb-env/bin/python docs/reaudit-2026-11-16/ch03/check-evidence/run_native.py --after
node docs/reaudit-2026-11-16/ch03/check-evidence/run_probes.mjs --after
```

`tasks-before.json` никогда не перезаписывается раннерами. Native after экспортирует текущие setup/check/solution в `tasks-after.json`; Pyodide after читает его. Пробы всегда используют зафиксированные исходные пользовательские программы с новыми setup/check, затем отдельно запускают актуальные авторские решения. Исходные ошибки приводятся в JSON как реальные `result.check.msg` и stdout, полные код/prepare/expected сохранены в каждой строке. `match` сравнивает именно ожидаемый и фактический зачёт; отказ корректной программы не скрывается как ошибка тестовой инфраструктуры.

`run_probes.mjs` загружает пакеты pandas/matplotlib/openpyxl из `site/assets/vendor/pyodide/`, исполняет подготовку CSV/Excel в `/home/pyodide` и перед каждой пробой восстанавливает необходимые исходные файлы. Временные результаты не попадают в progress и не являются студенческими артефактами.

[Реестр C03-01…16 и учебные критерии](../checks.md). Машиночитаемые хеши экспортов и числа — в [checks-summary.json](checks-summary.json). Штатные проверки и ноутбуки координатора лежат рядом и имеют отдельные знаменатели.
