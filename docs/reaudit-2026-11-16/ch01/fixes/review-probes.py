"""Из корня: .venv/bin/python docs/reaudit-2026-11-16/ch01/fixes/review-probes.py /tmp/fresh.json"""
from contextlib import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
from collections import Counter
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'site/assets'))
from harness import run

tasks = {t['lesson'][5:] + '/' + t['id']: t for t in json.loads(Path(sys.argv[1]).read_text())
         if t['kind'] == 'task' and t['lesson'].startswith('ch01/')}
default = (ROOT / 'site/data/orders.csv').read_bytes()
april = (HERE.parent / 'student/transfer/orders.csv').read_bytes()
march = (HERE / 'student/transfer/orders.csv').read_bytes()
header = b'order_id,date,city,drink,amount\n'
checks = []


def trial(name, key, code, expected=True, data=default):
    spec = tasks[key]
    with TemporaryDirectory() as tmp, chdir(tmp):
        Path('orders.csv').write_bytes(data)
        result = run(code, spec['check'], spec['setup'])
        actual = result['check']['passed']
        note = result['check']['msg']
        report = Path('report.md').read_text() if Path('report.md').is_file() else ''
    print(f'{name} | {key} | {expected=} {actual=} | {note}')
    checks.append(expected == actual)
    return report


def starter(key, tail):
    return tasks[key]['starter'] + '\n' + tail


def saved(filename):
    return (HERE / 'student' / filename).read_text()


print('CPython', sys.version.split()[0])
print('SHA256 экспорт', hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
for line in saved('attempts.jsonl').splitlines():
    rec = json.loads(line)
    if rec['action'] == 'grade' and rec['id'] in tasks:
        trial('UI ' + rec['at'], rec['id'], rec['code'], rec['passed'])

for tail, want in [('kazan_cups=sales[1][1]', True),
                   ('city_record=sales[1]\nkazan_cups=city_record[1]', True),
                   ('kazan_cups=538', False), ('kazan_cups=sales[1][2]', False)]:
    trial('M2 ' + tail.splitlines()[-1], '07-tables/cell', starter('07-tables/cell', tail), want)

for key, pos, neg in [
    ('07-tables/best-city', 'best_city=max(sales, key=lambda r:r[2]*r[1])[0]',
     'best_city=max(sales,key=lambda r:r[1])[0]'),
    ('08-dicts/top', 'top_count=-1\nfor d,n in counts.items():\n if top_count<n: top_count,top_drink=n,d',
     'top_drink=""\nfor d,n in counts.items():\n if d>top_drink: top_drink,top_count=d,n'),
    ('11-comprehensions/top-key', 'top=max(counts,key=lambda drink:counts[drink])','top=max(counts,key=len)'),
    ('12-errors/skip-bad', 'valid=[]\nfor s in raw:\n try: valid.append(int(s))\n except ValueError: pass\ntotal=sum(valid)\nbad=len(raw)-len(valid)',
     'valid=[int(s) for s in raw if s.isdigit()]\ntotal=sum(valid)\nbad=len(raw)-len(valid)')]:
    trial('E02/M1' if 'skip' not in key else 'C04', key, starter(key, pos))
    trial('Подмена', key, starter(key, neg), False)

historical = [json.loads(s) for s in (HERE.parent / 'technical/regression-ch01-programs.jsonl').read_text().splitlines()]
for h in historical:
    trial('T01 ' + h['description'], 'exam-1/parse', h['code'], h['expected'])
mapped = historical[0]['code']
joint = mapped.replace('text = ', 'text, total = ').replace('\nrows = ', ', 0\nrows = ')
trial('C01 совместное + map', 'exam-1/parse', joint)
trial('C01 вложенная распаковка', 'exam-1/parse', joint.replace('text, total = ', '(text,), total = (').replace(', 0\nrows', ',), 0\nrows'))
for field in ['qty','unit']:
    trial('C02 float ' + field, 'exam-1/parse', joint.replace(f'int({field})', f'float({field})'), False)

group = """def revenue_by(rows,key):
    sums={}
    for row in rows:
        label=row[key]
        sums[label]=sums.get(label,0)+row['amount']
    return sums"""
trial('CW-CP-01 только определение', 'exam-1/revenue-by', group)
trial('CW-CP-01 всегда по городам', 'exam-1/revenue-by', group.replace('row[key]', "row['city']"), False)

style = saved('long-line.py')
for width in [79,80,84]:
    trial(f'E03 {width}', '09b-style/long-line',style + '\n#' + 'x'*(width-1),width == 79)

first_rule = """by_id = {}
for row in orders:
    by_id.setdefault(row['order_id'],row)
clean=list(by_id.values())
n_dupes=len(orders)-len(clean)"""
last_rule = first_rule.replace("by_id.setdefault(row['order_id'],row)", "by_id[row['order_id']]=row")
trial('C03 первый в исходном порядке', '14-project/dedupe', first_rule)
trial('C03 последняя версия, порядок ключей прежний', '14-project/dedupe', last_rule, False)

file = saved('monthly-report.py')
report = saved('report.py')
for note, data in [('V-13 апрель',april), ('B-103 март',march)]:
    out = trial('ST-01/R-02, R-01 ' + note,'14-project/file',file,data=data)
    print(out.strip())
    if data == march:
        assert out == saved('transfer/report.md')

last_file = file.replace('            continue\n        first[order_id]', "            clean[clean.index(old)] = row\n            first[order_id] = row\n            continue\n        first[order_id]")
assert last_file != file
trial('C03 шаг 8 последнее читаемое значение','14-project/file',last_file,False)
swapped = file.replace("{old['amount']} ₽;", "{row['amount']} ₽;").replace("{row['amount']} ₽ (отличаются", "{old['amount']} ₽ (отличаются")
trial('ST-01 перепутаны роли двух сумм','14-project/file',swapped,False,april)
trial('ST-01 предупреждение удалено','14-project/file',file.replace('journal.extend(conflicts)',''),False,april)
own_words = file.replace('Конфликт {order_id}: учтена первая читаемая запись', '{order_id}: приняли первый чек').replace('другая запись', 'поздняя запись')
trial('ST-01 собственное пояснение','14-project/file',own_words,True,april)

for month in ['11','12',None]:
    dat = header
    if month:
        dat += f'A,2027-{month}-02,Тула,Чай,\nB,2027-{month}-03,Тула,Чай,—\n'.encode()
    out = trial('E01 '+str(month),'14-project/file',file,True,dat)
    lines = out.splitlines()
    assert lines[0] == ('# Отчёт за 2027-'+month if month else '# Отчёт')
    assert 'Нет принятых заказов' in lines and 'Средний чек' not in out
    print(lines[0], '|', lines[1])
trial('E01 прежний вывод без месяца на датах','14-project/file',file.replace('if not clean and period:', 'if False:'),False)

names = ['Ёжевичный чай','Американо','Бабл-ти','Дарджилинг']
ties = header + ''.join(f'F{i},2027-02-0{i},Тула,{d},30\n' for i,d in enumerate(names,1)).encode()
alternate_top = saved('drinks.py').replace(
    "sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))",
    "sorted(sorted(counts.items()), key=lambda pair: pair[1], reverse=True)")
trial('E04 два устойчивых прохода', '14-project/drinks', alternate_top, True, ties)
trial('E04 словарная перестановка в шаге 5', '14-project/drinks',
      saved('drinks.py').replace('(-pair[1], pair[0])', '(-pair[1], pair[0].replace("Ё", "Е~"))'),
      False, ties)
out = trial('E04 четыре равных частоты','14-project/file',file,True,ties)
print(out.splitlines()[5:7])
assert ', '.join(f'{name} (1)' for name in names[:3]) in out
rus = file.replace('(-pair[1], pair[0])', '(-pair[1], pair[0].replace("Ё", "Е~"))')
trial('E04 иной порядок Ё/А','14-project/file',rus,False,ties)
for label, want in [
    ('Топ-3 напитков по количеству заказов:',True),
    ('Три самых частых напитка по числу заказов:',True),
    ('Топ-3 напитка по числу принятых заказов - ',True),
    ('Напитки:',False),
    ('Топ-3 напитка по сумме заказов:',False)]:
    trial('R-01 '+label,'14-project/report',report.replace('Топ-3 напитка по числу принятых заказов:', label),want)
for original, alternative in [('Лучший город:', 'Город с наибольшей выручкой:'),
                              ('Средний чек:', 'Средний чек по принятым заказам:')]:
    trial('Своя подпись ' + alternative, '14-project/report', report.replace(original, alternative))
    trial('Та же подпись в полном файле ' + alternative, '14-project/file',
          file.replace(original, alternative), True, march)
trial('Обе подписи в реальной финальной посылке', '14-project/report', saved('report-natural-labels.py'))
trial('Своя подпись среднего, но другая сумма', '14-project/report',
      saved('report-natural-labels.py').replace('revenue / len(orders)', 'revenue / len(orders) + 10'), False)

seen = set()
cities = Counter()
duplicates = []
with (ROOT / 'site/data/orders.csv').open() as source:
    for order in csv.DictReader(source):
        try:
            amount = int(order['amount'])
        except ValueError:
            continue
        if order['order_id'] in seen:
            duplicates.append((order['order_id'], order['city'], amount))
        else:
            seen.add(order['order_id'])
            cities[order['city']] += amount
assert duplicates == [('Z-1038', 'Пермь', 450)]
assert cities['Пермь'] == 5270 and cities['Казань'] == 5770
print('Мини-тест о дубле', duplicates, cities['Пермь'] + 450, '<', cities['Казань'])
trial('R-01 неверный остаток','14-project/report',report.replace(' = len(orders) - sum(', ' = 1 + len(orders) - sum('),False)

print('Q02',12/3,type(12/3).__name__)
print('Q06',[(n, bool(n)) for n in (0,1)])
try:
    compile('if revenue = plan: pass','<Q06>','exec')
except SyntaxError:
    print('Q06 = → SyntaxError')
else:
    raise AssertionError('assignment in conditional')
for key in ['07-tables/cell','07-tables/best-city','08-dicts/top','11-comprehensions/top-key','exam-1/parse','12-errors/skip-bad','14-project/dedupe','14-project/report','14-project/file']:
    print('SHA256', key, hashlib.sha256(tasks[key]['check'].encode()).hexdigest())
print(f'{sum(checks)} из {len(checks)} вердиктов совпали с ожиданием.')
sys.exit(0 if all(checks) else 1)
