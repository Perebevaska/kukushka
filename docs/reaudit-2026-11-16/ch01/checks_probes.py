"""Independent limited probes, authored before execution. No course edits/build.

Run from the repository root:
  .venv/bin/python docs/reaudit-2026-11-16/ch01/checks_probes.py
  node docs/reaudit-2026-11-16/ch01/checks_runner.mjs
  .venv/bin/python docs/reaudit-2026-11-16/ch01/checks_probes.py --native
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/checks'))
from acceptance_runner import Chapter
import harness

REPORT = '''from collections import Counter

def build_report(orders):
    if not orders:
        return '# Отчёт\\nНет принятых заказов'
    cities, days, drinks = Counter(), Counter(), Counter()
    for o in orders:
        cities[o['city']] += o['amount']
        days[o['date'].weekday()] += o['amount']
        drinks[o['drink']] += 1
    city = max(cities, key=cities.get)
    day = max(days, key=days.get)
    day_names = ('понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье')
    total = sum(o['amount'] for o in orders)
    top = sorted(drinks.items(), key=lambda x: (-x[1], x[0]))[:3]
    drink_text = ', '.join(f'{name} ({count})' for name, count in top)
    date = orders[0]['date']
    return '\\n'.join([
        f'# Отчёт за {date:%Y-%m}',
        f'День с наибольшей выручкой — {day_names[day]} — {days[day]} руб.',
        f'Средний чек — {round(total / len(orders))} рублей',
        f'Учтённая выручка — {total} ₽',
        f'Лучший город — {city} — {cities[city]} руб.',
        f'Напитки по числу заказов — {drink_text}',
        f'Принято заказов — {len(orders)}',
    ])
'''
LOAD = '''import csv
import datetime as dt
from pathlib import Path

orders = []
n_bad = 0
with open('orders.csv', encoding='utf-8', newline='') as f:
    for o in csv.DictReader(f):
        try:
            o['amount'] = int(o['amount'])
        except ValueError:
            n_bad += 1
            continue
        o['date'] = dt.date.fromisoformat(o['date'])
        orders.append(o)
by_id = {}
for o in orders:
    by_id.setdefault(o['order_id'], o)
clean = list(by_id.values())
n_dupes = len(orders) - len(clean)
journal = '\\n'.join([
    '## Качество данных',
    f'- Строк в выгрузке: {len(orders) + n_bad}',
    f'- Битых строк: {n_bad}',
    f'- Дублей: {n_dupes}',
])
Path('report.md').write_text(build_report(clean) + '\\n\\n' + journal + '\\n', encoding='utf-8')
'''
PARSER = '''def parse_line(line):
    city, cups, price = line.split(';')
    return [city, int(cups), int(price)]

text = 'Пермь;412;205\\nКазань;538;198\\n\\nТюмень;297;214\\n'
'''
CALC = "rows = map(parse_line, filter(None, text.splitlines()))\ntotal = sum(cups * price for city, cups, price in rows)\n"


def cases():
    rows = []
    def add(id, lesson, task, description, code, expected, **extra):
        rows.append(dict(id=id, lesson='ch01/' + lesson, task=task,
                         description=description, code=code, expected=expected, **extra))
    add('C-P01', 'exam-1', 'parse', 'map with integer parser', PARSER + CALC, True)
    add('C-P02', 'exam-1', 'parse', 'csv.reader parser, alias passed into map',
        PARSER.replace("city, cups, price = line.split(';')", "import csv\n    city, cups, price = next(csv.reader([line], delimiter=';'))")
        + CALC.replace('rows = map(parse_line', 'parser = parse_line\nrows = map(parser'), True)
    add('C-P03', 'exam-1', 'parse', 'float parser violates explicit int types',
        (PARSER + CALC).replace('int(cups), int(price)', 'float(cups), float(price)'), False)
    add('C-P04', 'exam-1', 'parse', 'inline parsing instead of using required function',
        PARSER + "total = sum(int(s.split(';')[1]) * int(s.split(';')[2]) for s in text.splitlines() if s)\n", False)
    add('C-P05', 'exam-1', 'parse', 'tuple assignment of input and accumulator, valid computation',
        PARSER.replace("text = ", "text, total = ").rstrip() + ", 0\n"
        + "for line in text.splitlines():\n    if line:\n        _, cups, price = parse_line(line)\n        total += cups * price\n", True)
    add('C-R01', 'exam-1', 'revenue-by', 'defaultdict, definition only',
        "from collections import defaultdict\ndef revenue_by(orders, field):\n    totals = defaultdict(int)\n    for row in orders:\n        totals[row[field]] += row['amount']\n    return dict(totals)\n", True)
    add('C-R02', 'exam-1', 'revenue-by', 'sorting and groupby',
        "from itertools import groupby\ndef revenue_by(orders, field):\n    key = lambda row: row[field]\n    return {k: sum(o['amount'] for o in rows) for k, rows in groupby(sorted(orders, key=key), key=key)}\n", True)
    add('C-R03', 'exam-1', 'revenue-by', 'last amount instead of sum',
        "def revenue_by(orders, field):\n    return {o[field]: o['amount'] for o in orders}\n", False)
    add('C-R04', 'exam-1', 'revenue-by', 'mutable default accumulates previous calls',
        "def revenue_by(orders, field, totals={}):\n    for o in orders:\n        totals[o[field]] = totals.get(o[field], 0) + o['amount']\n    return totals\n", False)
    add('C-T01', '14-project', 'report', 'independent Counter solution with reordered lines and dashes', REPORT, True)
    add('C-T02', '14-project', 'report', 'average and revenue labels swapped',
        REPORT.replace("f'Средний чек — {round(total / len(orders))} рублей'", "f'Учтённая выручка — {round(total / len(orders))} рублей'")
        .replace("f'Учтённая выручка — {total} ₽'", "f'Средний чек — {total} ₽'"), False)
    add('C-T03', '14-project', 'report', 'best day by order count instead of revenue',
        REPORT.replace("days[o['date'].weekday()] += o['amount']", "days[o['date'].weekday()] += 1"), False)
    add('C-T04', '14-project', 'report', 'Russian month header explicitly allowed',
        REPORT.replace("f'# Отчёт за {date:%Y-%m}'", "f\"# Отчёт за {('январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')[date.month-1]} {date.year}\""), True)
    add('C-T05', '14-project', 'report', 'choose last winner on revenue tie',
        REPORT.replace('max(cities, key=cities.get)', 'max(reversed(list(cities)), key=cities.get)')
        .replace('max(days, key=days.get)', 'max(reversed(list(days)), key=days.get)'), True)
    add('C-F01', '14-project', 'file', 'independent pathlib writer, first duplicate via setdefault', REPORT + LOAD, True)
    add('C-F02', '14-project', 'file', 'last duplicate wins, violates keep-first rule on conflicting duplicate',
        REPORT + LOAD.replace("by_id.setdefault(o['order_id'], o)", "by_id[o['order_id']] = o"), False)
    add('C-F03', '14-project', 'file', 'append instead of overwrite',
        REPORT + LOAD.replace("Path('report.md').write_text(build_report(clean) + '\\n\\n' + journal + '\\n', encoding='utf-8')",
            "with open('report.md', 'a', encoding='utf-8') as f:\n    f.write(build_report(clean) + '\\n\\n' + journal + '\\n')"), False)
    conflict = ('order_id,date,city,drink,amount\n'
                'O1,2027-10-04,Томск,Чай,260\n'
                'O2,2027-10-05,Омск,Какао,690\n'
                'O3,2027-10-04,Томск,Чай,230\n'
                'O3,2027-10-04,Томск,Чай,1230\n'
                'O4,2027-10-05,Омск,Матча,—\n'
                'O5,2027-10-06,Томск,Матча,85\n'
                'O2,2027-10-05,Омск,Какао,690\n')
    add('C-F04', '14-project', 'file', 'first-wins on conflicting duplicate in new monthly CSV',
        REPORT + LOAD, True, files_override={'orders.csv': conflict})
    add('C-F05', '14-project', 'file', 'last-wins on same conflicting duplicate in new monthly CSV',
        REPORT + LOAD.replace("by_id.setdefault(o['order_id'], o)", "by_id[o['order_id']] = o"),
        False, files_override={'orders.csv': conflict})
    # Previously unflagged card: distinguishes exception semantics from digit filtering.
    SKIP = "raw = ['450', '320', '', '1180', '—', '275', '1 250', '640']\ntotal = bad = 0\n"
    add('C-N01', '12-errors', 'skip-bad', 'alternative int conversion with explicit ValueError counter',
        SKIP + "for value in raw:\n    try:\n        number = int(value)\n    except ValueError:\n        bad += 1\n    else:\n        total += number\n", True)
    add('C-N02', '12-errors', 'skip-bad', 'isdigit rejects valid signed or whitespace-padded integer text',
        SKIP + "for value in raw:\n    if value.isdigit():\n        total += int(value)\n    else:\n        bad += 1\n", False)
    for id, wrong in [('C-N03', False), ('C-N04', True)]:
        probe_code = (SKIP + ("for value in raw:\n    if value.isdigit():\n        total += int(value)\n    else:\n        bad += 1\n" if wrong else
            "for value in raw:\n    try:\n        number = int(value)\n    except ValueError:\n        bad += 1\n    else:\n        total += number\n"))
        probe_code = probe_code.replace("['450', '320', '', '1180', '—', '275', '1 250', '640']", "[' -50 ', '+20', '30', '60']")
        add(id, '12-errors', 'skip-bad', 'transfer: signed and padded int text, ' + ('isdigit' if wrong else 'int'),
            probe_code, not wrong, check_override="assert need('total') == 60, f'total = {need(\"total\")}; int accepts all four strings, sum should be 60'\nassert need('bad') == 0, f'bad = {need(\"bad\")}; int accepts all four strings'\n")
    return rows


def main():
    rows = cases()
    with Chapter('ch01') as chapter:
        selected = {(r['lesson'], r['task']) for r in rows}
        tasks = [{**item, 'lesson': 'ch01/' + lesson} for (lesson, task), item in chapter.tasks.items()
                 if ('ch01/' + lesson, task) in selected]
    (OUT / 'checks_tasks.json').write_text(json.dumps(tasks, ensure_ascii=False), encoding='utf-8')
    (OUT / 'checks_programs.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    if '--native' not in sys.argv:
        print(f'Prepared {len(rows)} independent probes before execution.')
        return
    by_id = {t['lesson'] + '/' + t['id']: t for t in tasks}
    results = []
    for row in rows:
        item = by_id[row['lesson'] + '/' + row['task']]
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                for file in item['files']:
                    shutil.copy(ROOT / 'site/data' / file, file)
                for file, text in row.get('files_override', {}).items():
                    Path(file).write_text(text, encoding='utf-8')
                result = harness.run(row['code'], row.get('check_override', item['check']), item.get('setup'), False)
                artifact = Path('report.md').read_text(encoding='utf-8') if Path('report.md').is_file() else None
            finally:
                os.chdir(previous)
        record = {**row, 'runtime': sys.version, 'result': result, 'report_md': artifact}
        results.append(record)
        print(row['id'], row['expected'], result.get('check'))
    (OUT / 'checks_native.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in results), encoding='utf-8')


if __name__ == '__main__':
    main()
