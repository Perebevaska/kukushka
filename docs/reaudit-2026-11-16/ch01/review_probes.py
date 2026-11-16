"""Запуск из корня репозитория: python3 путь/к/review_probes.py <экспорт build.py>."""
from collections import Counter
from contextlib import chdir
import csv
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'site/assets'))
from harness import run

tasks = {(t['lesson'].split('/')[-1], t['id']): t
         for t in json.loads(Path(sys.argv[1]).read_text()) if t['kind'] == 'task' and t['lesson'].startswith('ch01/')}
source = (ROOT / 'site/data/orders.csv').read_bytes()
transfer = (HERE / 'student/transfer/orders.csv').read_bytes()
student = (HERE / 'student/transfer/project_report.py').read_text()
header = 'order_id,date,city,drink,amount\n'
print('CPython', sys.version.split()[0])


def grade(lesson, task, code, data=source):
    spec = tasks[lesson, task]
    with TemporaryDirectory() as tmp, chdir(tmp):
        Path('orders.csv').write_bytes(data)
        check = run(code, spec['check'], spec['setup'])['check']
        report = Path('report.md')
        return check['passed'], check['msg'], report.read_text() if report.exists() else ''


def probe(name, lesson, task, code, expected, data=source):
    passed, msg, report = grade(lesson, task, code, data)
    print(name, 'задача:', lesson, task, 'зачёт:', passed, msg)
    assert passed == expected, (name, passed, expected)
    return report


def starter(lesson, task):
    return tasks[lesson, task]['starter'] + '\n'


def solution(lesson, task):
    return tasks[lesson, task]['solution']


cell = starter('07-tables', 'cell')
for tail, expected in [('kazan_cups=sales[1][1]', True),
                       ('city_record=sales[1]\nkazan_cups=city_record[1]', False)]:
    probe('M2', '07-tables', 'cell', cell + tail, expected)
for lesson, task, tail in [
    ('07-tables', 'best-city', 'best_city = max(sales, key=lambda s:s[1])[0]'),
    ('08-dicts', 'top', 'top_drink=""\nfor drink,n in counts.items():\n    if drink > top_drink: top_drink,top_count=drink,n'),
    ('11-comprehensions', 'top-key', 'top=max(counts,key=len)'),
]:
    probe('E02, верное', lesson, task, solution(lesson, task), True)
    probe('E02, чужой признак', lesson, task, starter(lesson, task) + tail, True)

print('E02/M1, Пермь при 520 чашках:', 520*205, 'Казань:', 538*198)
# Три разных победителя по названию, длине и количеству.
counts = {'Айс': 17, 'Матча-латте': 1, 'Ямс': 2}
print('E02, частота/имя/длина:', max(counts,key=counts.get), max(counts), max(counts,key=len))
text = 'Пермь;412;205\nКазань;538;198\n\nТюмень;297;214\n'
parser = """def parse_line(line):
    c,n,p=line.split(';')
    return [c,int(n),int(p)]
"""
calc = """
records=map(parse_line, filter(None, text.splitlines()))
total = sum(count*price for city,count,price in records)
"""
for name, p, binding, expected in [
    ('старый T01', parser, f'text = {text!r}', True),
    ('C01', parser, f'text, total = {text!r}, 0', False),
    ('C02', parser.replace('int(', 'float('), f'text = {text!r}', True),
]:
    probe(name, 'exam-1','parse',p + binding + calc, expected)
group = """def revenue_by(rows,key):
    result={}
    for row in rows:
        value=row[key]
        result[value]=result.get(value,0)+row['amount']
    return result"""
probe('старый CW-CP-01', 'exam-1','revenue-by',group,True)
string_rule = """total=bad=0
for v in raw:
    if v.isdigit(): total+=int(v)
    else: bad+=1"""
probe('C04', '12-errors', 'skip-bad', starter('12-errors', 'skip-bad')+string_rule, True)
items = [' -50 ', '+20', '30', '60']
print('C04, int / isdigit:', sum(map(int, items)), 0,
      sum(int(v) for v in items if v.isdigit()), sum(not v.isdigit() for v in items))

last = student.replace('for o in orders:\n    if o["order_id"]', 'for o in reversed(orders):\n    if o["order_id"]', 1)
assert last != student
for name, program, data, accepted in [
    ('C03 штатно первый',student,source,True), ('C03 штатно последний',last,source,True),
    ('C03 апрель первый',student,transfer,True), ('C03 апрель последний',last,transfer,False),
]:
    report = probe(name,'14-project','file',program,accepted,data)
    if data == transfer: print(report)

empty_reports = []
for month in ['11', '12']:
    data = (header + f'A,2027-{month}-02,Тула,Чай,\nB,2027-{month}-03,Тула,Чай,—\n').encode()
    empty_reports.append(probe('E01 месяц '+month,'14-project','file',student,True,data))
assert empty_reports[0] == empty_reports[1]
print('E01 одинаковый результат:',empty_reports[0])
only_header = probe('E01 только заголовок','14-project','file',student,True,header.encode())
assert 'Нет принятых заказов' in only_header and '2027-' not in only_header

data = header
for i,drink in enumerate(['Ёжевичный чай','Американо','Бабл-ти','Дарджилинг'],1):
    data += f'F{i},2027-02-0{i},Тула,{drink},30\n'
rus_key = student.replace('(-kv[1], kv[0])','(-kv[1], kv[0].replace("Ё", "Е~"))')
for name,prog,expected in [('кодовые точки',student, True),('русский порядок для этих четырёх',rus_key,False)]:
    report = probe('E04 '+name,'14-project','file',prog,expected,data.encode())
    print(next(line for line in report.splitlines() if line.startswith('Напитки')))

rows = list(csv.DictReader(io.StringIO(transfer.decode())))
by_id = {}
bad = []
for row in rows:
    try: row['amount'] = int(row['amount'])
    except ValueError:
        bad.append(row['order_id'])
        continue
    by_id.setdefault(row['order_id'], []).append(row)
first = [versions[0] for versions in by_id.values()]
print('ST-01/R-02, суммы по одному ID', {k: [r['amount'] for r in v] for k,v in by_id.items()})
print('строк/битые/дубли',len(rows),bad,sum(len(v)-1 for v in by_id.values()))
print('без спорной / первая / последняя', sum(v[0]['amount'] for v in by_id.values() if len(v)==1),
      sum(v[0]['amount'] for v in by_id.values()),sum(v[-1]['amount'] for v in by_id.values()))
print('R-01 все напитки:',Counter(r['drink'] for r in first))
print('Q02',12/3,type(12/3).__name__)
print('Q06', bool(1))
try: compile('if revenue = plan: pass', '<пример>', 'exec')
except SyntaxError as e: print('Q06',type(e).__name__)
style = solution('09b-style','long-line')+'\n#'+'x'*83
probe('E03 84 символа','09b-style','long-line',style,False)
# Независимый подсчёт по Markdown: в вариантах главы из inline-разметки встречаются только обратные кавычки.
import re
question_blocks = re.findall(r'^::: quiz [^\n]*\n(.*?)^:::', (ROOT/'content/ch01/test.md').read_text(), re.M | re.S)
longest = []
shortest = []
for idx, block in enumerate(question_blocks, 1):
    options = re.findall(r'^- \[([ x])\] (.*)$', block, re.M)
    assert len(options) == 4
    sizes = [len(s.replace('`', '')) for key, s in options]
    k = next(i for i,(key, s) in enumerate(options) if key == 'x')
    if sizes.count(max(sizes)) == 1 and sizes[k] == max(sizes):
        longest.append(idx)
    if sizes.count(min(sizes)) == 1 and sizes[k] == min(sizes):
        shortest.append(idx)
print('Длина по исходному Markdown, верный единственный длинный/короткий:', longest, shortest)
assert longest == [1,6,8,15] and shortest == [4]
print('Q12 перенос [100,250]:',[round(p*1.1) for p in [100,250] if p > 200])
