#!/usr/bin/env python3
"""Учебные блокноты для уроков ch02/08 (устройство .ipynb) и ch02/10 (блокнот в git).

    python3 tools/gen_ch02_notebooks.py

Пишет два файла в site/data/:
  zerno_draft.ipynb  — черновик аналитика: ячейки выполнялись вразнобой, абсолютный путь,
                       ошибка в выводе, закомментированный код, вывод в тексте по устаревшему числу;
  zerno_rerun.ipynb  — тот же блокнот после исправления пути и «Restart Kernel and Run All Cells».

Числа в выводах ячеек считаются по site/data/orders_3m.csv. Случайности нет — файл всегда одинаковый.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'site' / 'data'

df = pd.read_csv(DATA / 'orders_3m.csv')
REV_ALL = int(df['amount'].sum())
REV_DELIVERY = int(df.loc[df['channel'] == 'доставка', 'amount'].sum())

META = {
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.12.7'},
}

TB_KEYERROR = [
    '---------------------------------------------------------------------------',
    'KeyError                                  Traceback (most recent call last)',
    'Cell In[{n}], line 1',
    '----> 1 df.groupby("shop")["amount"].sum()',
    '',
    'File .../pandas/core/groupby/grouper.py:901, in get_grouper(obj, key, level, sort, observed, validate, dropna)',
    '--> 901         raise KeyError(gpr)',
    '',
    "KeyError: 'shop'",
]


def md(cid, text):
    return {'cell_type': 'markdown', 'id': cid, 'metadata': {}, 'source': text.splitlines(keepends=True)}


def code(cid, text, n=None, outputs=None):
    return {'cell_type': 'code', 'execution_count': n, 'id': cid, 'metadata': {},
            'outputs': outputs or [], 'source': text.splitlines(keepends=True)}


def result(n, value):
    return [{'output_type': 'execute_result', 'execution_count': n, 'metadata': {},
             'data': {'text/plain': [str(value)]}}]


def error(n):
    return [{'output_type': 'error', 'ename': 'KeyError', 'evalue': "'shop'",
             'traceback': [line.replace('{n}', str(n)) for line in TB_KEYERROR]}]


def notebook(path_line, counts, sum_value, conclusion):
    c_imp, c_read, c_filter, c_sum, c_group = counts
    cells = [
        md('a1', '# Осень\n'),
        code('a2', 'import pandas as pd', c_imp),
        code('a3', path_line, c_read),
        code('a4', 'df = df[df["channel"] == "доставка"]', c_filter),
        code('a5', 'df["amount"].sum()', c_sum, result(c_sum, sum_value)),
        code('a6', 'df.groupby("shop")["amount"].sum()', c_group, error(c_group)),
        code('a7', '# import matplotlib.pyplot as plt\n# df.plot(x="datetime", y="amount")\n# plt.show()'),
        md('a8', conclusion),
    ]
    return {'cells': cells, 'metadata': META, 'nbformat': 4, 'nbformat_minor': 5}


def save(name, nb):
    text = json.dumps(nb, ensure_ascii=False, indent=1) + '\n'
    (DATA / name).write_text(text, encoding='utf-8')
    print(f'{name}: {len(nb["cells"])} ячеек, {len(text.splitlines())} строк JSON')


conclusion = f'## Выводы\n\nВыручка доставки за осень — {REV_ALL:,} ₽.\n'.replace(',', ' ')
# черновик: ячейки запускали вразнобой — сумму посчитали ДО фильтра доставки
save('zerno_draft.ipynb', notebook('df = pd.read_csv("/Users/anya/Downloads/orders_3m.csv")',
                                   (1, 2, 6, 3, 7), REV_ALL, conclusion))
# тот же блокнот: путь исправлен, Restart & Run All — счётчики по порядку, сумма теперь по доставке
save('zerno_rerun.ipynb', notebook('df = pd.read_csv("data/orders_3m.csv")',
                                   (1, 2, 3, 4, 5), REV_DELIVERY, conclusion))
print('выручка всей сети', REV_ALL, '· доставки', REV_DELIVERY)
