#!/usr/bin/env python3
"""Собрать архив курса, чтобы поделиться: dist/ds-course-ГГГГ-ММ-ДД.zip

В архив идут готовый сайт (с локальным Python для браузера — работает без интернета),
сервер и запускалки для Mac, Windows и Linux. Личный прогресс (progress/), исходники
уроков и служебные папки в архив НЕ попадают.

  python3 tools/pack.py            # сайт должен быть уже собран (tools/build.py) и блокноты (tools/make_notebooks.py)
  python3 tools/pack.py --list     # только показать, какие файлы попадут в архив
"""
from __future__ import annotations

import datetime as dt
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOP = 'ds-course'
FILES = ['Курс.command', 'Курс-Windows.bat', 'Курс-Linux.sh', 'КАК ЗАПУСТИТЬ.txt', 'LICENSE',
         'tools/serve.py', 'tools/get-python.ps1']
EXEC = {'Курс.command', 'Курс-Linux.sh'}
SKIP_NAMES = {'.DS_Store', '__pycache__', 'Thumbs.db',
              '_work', '.ipynb_checkpoints',    # рабочая папка и автосохранения Jupyter (site/notebooks)
              'catboost_info'}                  # логи обучения CatBoost после запуска блокнотов extra/
# Файлы, которые пишут примеры и задачи уроков (to_csv, open(..., "w")). Если урок однажды запустили
# с рабочей папкой site/data, они остаются там мусором — в архив их не кладём.
SKIP_DATA = {'t.csv', 'clients_clean.csv', 'report.txt', 'report.md', 'by_city.csv', 'для_excel.csv',
             'card.json', 'golden.csv', 'guests_copy.csv', 'clients.parquet', 'export.csv', 'export_14.csv',
             'export_2026-12-07.csv', 'runs.csv', 'passport.json', 'call_list.csv',
             'plan_2026-10-09.csv'}


def collect_items() -> list:
    """Файлы архива: запускалки + весь site/ (страницы, данные, блокноты site/notebooks) без служебного."""
    items = [ROOT / f for f in FILES]
    items += sorted(p for p in (ROOT / 'site').rglob('*') if p.is_file()
                    and not SKIP_NAMES & set(p.relative_to(ROOT).parts) and not p.name.startswith('_')
                    and not (p.parent == ROOT / 'site' / 'data' and p.name in SKIP_DATA))
    return items


def main() -> None:
    site = ROOT / 'site'
    if not (site / 'index.html').exists():
        sys.exit('Нет site/index.html — сначала соберите сайт: python3 tools/build.py')
    if not (site / 'assets/vendor/pyodide/pyodide.mjs').exists():
        sys.exit('Нет site/assets/vendor/pyodide — без него Python в браузере не запустится офлайн.')
    items = collect_items()
    if '--list' in sys.argv:          # что попадёт в архив, без самого архива
        for p in items:
            print(p.relative_to(ROOT).as_posix())
        return
    if not (site / 'notebooks' / 'dsc.py').exists():
        print('Внимание: нет site/notebooks — блокноты Jupyter не попадут в архив (python3 tools/make_notebooks.py).')
    out = ROOT / 'dist' / f'ds-course-{dt.date.today().isoformat()}.zip'
    out.parent.mkdir(exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in items:
            rel = p.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo.from_file(p, f'{TOP}/{rel}')
            mode = 0o755 if rel in EXEC else 0o644
            info.external_attr = (0o100000 | mode) << 16   # права сохраняются при распаковке на Mac/Linux
            info.compress_type = zipfile.ZIP_STORED if p.suffix in {'.whl', '.zip', '.wasm', '.woff2', '.png'} else zipfile.ZIP_DEFLATED
            with open(p, 'rb') as f:
                z.writestr(info, f.read())
            n += 1
    print(f'Готово: {out.relative_to(ROOT)} — {n} файлов, {out.stat().st_size / 2**20:.0f} МБ')


if __name__ == '__main__':
    main()
