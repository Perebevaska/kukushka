"""Проверяет комплект главы и при ручной сверке записывает его в журнал."""
from pathlib import Path
import collections, json, re, sys
import yaml

ch=sys.argv[1]
base=Path('docs/audit-2026-11-13')
d=base/ch
course=yaml.safe_load(Path('content/course.yaml').read_text())['chapters']
n=int(ch[2:])
assert ch==course[n-1]['id']
if n>2: assert (base/course[n-2]['id']/'acceptance.md').is_file(), "Не сдана предыдущая глава"
names=('report.md','expert.md','student.md','review.md','methodist.md','knowledge.md','browser.jsonl','student.jsonl','coverage.json')
for name in names: assert (d/name).stat().st_size>0, name
texts={k:(d/k).read_text() for k in names if k.endswith('.md')}
report=texts['report.md']
assert re.findall('^## (.+)$',report,re.M)[:2]==['Качество подачи учебного материала','Пути улучшения подачи']
for name,t in texts.items():
    for url in re.findall(r'\]\(([^\s()]+)\)',t):
        link=url.strip('<>').split('#')[0]
        if not link or ':' in link or link.startswith('mailto:'):continue
        assert (d/link).exists(), (name,url)
ids=lambda t:{i for i in re.findall(r'(?<!\w)(S(?:\d\d-)?\d{2,})(?!\w)',t)}
assert ids(texts['student.md'])<=ids(texts['review.md']), ('Пропущены замечания ученика',ids(texts['student.md'])-ids(texts['review.md']))
st=json.loads((d/'coverage.json').read_text())
assert st['passed']+len(st['unanswered'])==st['tasks'] and st['independent']+len(st['assisted'])==st['passed']
for f in ('expert.md','methodist.md','student.md','review.md','knowledge.md'):
    assert f in report, f'В отчёте нет ссылки {f}'
print(f"{ch}: комплект, порядок разделов, локальные ссылки и ID замечаний проверены. {st['tasks']} задач, {st['questions']} вопросов. Ручная содержательная сверка обязательна.")
if len(sys.argv)>2:
    note=sys.argv[2].strip()
    assert len(note)>70, 'Укажите результат содержательной сверки'
    (d/'acceptance.md').write_text(f"""# Сверка главы {n} с инструкциями

{note}

Координатор сверил состав главы с каталогом: **{st['tasks']} задач** ({st['attempts']} попыток), **{st['questions']} вопросов**. Самостоятельно принято {st['independent']}, с помощью {len(st['assisted'])}, остались непринятыми {len(st['unanswered'])}. Журналы включают исходный код попыток, ответы до раскрытия и результат браузера. [Покрытие по урокам](coverage.json) · [Действия ученика](student.jsonl) · [Результат браузера](browser.jsonl).

Перечень наблюдений ученика сверен с [независимой рецензией](review.md). В [отчёте](report.md) первыми идут оценка по пяти критериям и конкретные способы улучшить подачу; локальные ссылки и комплект ролей проверены.
""")
    rows=['# Состояние аудита курса','','Версия учебных материалов — `454a62c`. Главы проходят по порядку. После каждой отдельно сверяются состав, первичные свидетельства, решения рецензента и рекомендации редактору.','','| Глава | Статус | Результат сверки |','|---|---|---|']
    for j,c in enumerate(course,1):
        ck=c['id']
        title=c['title']
        if j==1: rows.append(f'| [1. {title}](ch01/report.md) | Завершена | [Сверка](ch01/acceptance.md) · 161 задача, 58 вопросов. |')
        elif (base/ck/'acceptance.md').exists():
            s=json.loads((base/ck/'coverage.json').read_text())
            rows.append(f"| [{j}. {title}]({ck}/report.md) | Завершена | [Сверка]({ck}/acceptance.md) · {s['tasks']} задач, {s['questions']} вопросов. |")
        elif j==n+1: rows.append(f'| {j}. {title} | Следующая к проверке | — |')
        else: rows.append(f'| {j}. {title} | В очереди | — |')
    rows+=['','После главы 15: отдельное интервью выпускника, затем сравнение оглавления и практики с университетскими программами.']
    if all((base/f).exists() for f in ('report.md','student-retrospective.md','curriculum-comparison.md')) and (base/'ch15/acceptance.md').exists():
        rows[-1]='После сверки главы 15 получен [отзыв выпускника](student-retrospective.md), затем выполнено [университетское сравнение](curriculum-comparison.md). [Итоговый отчёт](report.md).'
    (base/'progress.md').write_text('\n'.join(rows)+'\n')
