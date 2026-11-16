"""Регрессии проекта главы 1: python tools/checks/ch01_project_acceptance.py.

Читает исходные карточки; пишет только во временный каталог, не собирает сайт.
Контрольные CSV должны совпадать с данными, встроенными в ученические проверки.
"""
from contextlib import chdir
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from acceptance_runner import Chapter, ROOT
import harness


def main():
    sample = {}
    exec((ROOT / 'tools/checks/ch01_order_sample.py').read_text(), sample)
    names = ('october', 'november_bad', 'december_bad', 'header_only')
    for name, (_, text) in zip(names, sample['_project_file_cases']):
        assert (ROOT / f'tools/checks/fixtures/ch01_orders_{name}.csv').read_text() == text
    total = 0
    with Chapter('ch01') as chapter:
        tasks = {task: item for (lesson, task), item in chapter.tasks.items() if lesson == '14-project'}
        original = (ROOT / 'site/data/orders.csv').read_bytes()

        def probe(name, task, code=None, expected=True, data=original):
            nonlocal total
            item = tasks[task]
            with TemporaryDirectory() as directory, chdir(directory):
                Path('orders.csv').write_bytes(data)
                result = harness.run(code or item['solution'], item['check'], item.get('setup'), False)
                assert result.get('ok'), (name, result)
                check = result.get('check', {})
                assert bool(check.get('passed')) == expected, (name, expected, result)
                print(f'{name}: {"ACCEPT" if check["passed"] else "REJECT"}; {check.get("msg", "")}')
                total += 1
                return Path('report.md').read_text() if Path('report.md').exists() else ''

        for task in tasks:
            probe(f'author-{task}', task)

        probe('dedupe-setdefault-alternative', 'dedupe', '''first = {}
for row in orders:
    first.setdefault(row['order_id'], row)
clean = list(first.values())
n_dupes = len(orders) - len(clean)
''')
        probe('dedupe-last-copy', 'dedupe', '''clean = list({row['order_id']: row for row in orders}.values())
n_dupes = len(orders) - len(clean)
''', False)
        drinks = tasks['drinks']['solution']
        probe('drinks-russian-alphabet', 'drinks', drinks.replace('kv[0])', 'kv[0].replace("Ё", "Е"))'), False)
        report = tasks['report']['solution']
        # Presentation and wording are free within the stated meaning.
        own_report = report.replace('Принято заказов:', 'Количество принятых заказов:')
        own_report = own_report.replace('Учтённая выручка:', 'Выручка по принятым заказам:')
        own_report = own_report.replace('Лучший город:', 'Город-лидер:')
        own_report = own_report.replace('Топ-3 напитка по числу принятых заказов:', 'Топ 3 напитков по количеству заказов:')
        own_report = own_report.replace('Заказов остальных напитков:', 'Остальные напитки:')
        own_report = own_report.replace('День с наибольшей выручкой:', 'Лучший день по выручке:')
        own_report = own_report.replace('return "\\n".join(lines)', 'return "\\n".join([lines[0]] + list(reversed(lines[1:])))')
        probe('report-own-labels-and-order', 'report', own_report)
        for before, after in [('Средний чек', 'Средний чек по принятым заказам'),
                              ('Лучший город', 'Город с наибольшей выручкой')]:
            probe('report-label-' + after, 'report', report.replace(before + ':', after + ':'))

        probe('report-own-dashes', 'report', report.replace('return "\\n".join(lines)', 'return "\\n".join(line.replace(":", " —", 1) for line in lines)'))
        for label, expected in [
            ('Три самых частых напитка по числу заказов', True),
            ('Топ-3 напитка по сумме заказов', False),
            ('Топ-3 напитка по выручке', False),
        ]:
            probe('report-label-' + label, 'report', report.replace('Топ-3 напитка по числу принятых заказов', label), expected)
        for separator in (' - ', ' — ', ' – ', ' | '):
            variant = report.replace('return "\\n".join(lines)',
                                     'return "\\n".join(line.replace(": ", ' + repr(separator) + ', 1) for line in lines)')
            probe('report-separator-' + separator.strip(), 'report', variant)
        for label, expected in [
            ('Заказы напитков вне тройки', True),
            ('Число заказов остальных напитков', True),
            ('Сумма заказов остальных напитков', False),
            ('Число остальных напитков', False),
        ]:
            probe('report-rest-label-' + label, 'report', report.replace('Заказов остальных напитков', label), expected)
        probe('report-missing-rest', 'report', report + '''
_original_build = build_report
def build_report(orders):
    return "\\n".join(line for line in _original_build(orders).splitlines() if not line.startswith('Заказов остальных'))
''', False)
        probe('report-wrong-rest', 'report', report.replace('len(orders) - sum(count for drink, count in top3)', '0'), False)
        probe('report-unclear-top-label', 'report', report.replace('Топ-3 напитка по числу принятых заказов', 'Напитки по числу заказов'), False)
        probe('report-alphabet-mistake', 'report', report.replace('pair[0])', 'pair[0].replace("Ё", "Е"))'), False)
        file = tasks['file']['solution']
        october = sample['_project_file_cases'][0][1].encode()
        probe('file-last-readable', 'file', file.replace('        first = first_by_id[order_id]', '        first = first_by_id[order_id]\n        clean[clean.index(first)] = row'), False)
        preclean = file.replace('period = None', 'period = None\nseen_before_cleaning = set()').replace(
            '        period = row["date"][:7]',
            '        if row["order_id"] in seen_before_cleaning:\n            continue\n        seen_before_cleaning.add(row["order_id"])\n        period = row["date"][:7]')
        probe('file-dedupe-before-cleaning', 'file', preclean, False)
        own_file = file.replace('f"- Конфликт {order_id}: учтена первая читаемая запись', 'f"- Спорный заказ {order_id}: взята первая корректная строка')
        own_file = own_file.replace('другая запись', 'вторая запись').replace('Запросить первичный чек.', 'Сверить по первичному документу.')
        own_file = own_file.replace('Полная выручка неизвестна:', 'Полную выручку определить нельзя:')
        own_file = own_file.replace('Точных повторов:', 'Точных дублей:').replace('Конфликтующих строк:', 'Конфликтов:')
        probe('file-own-notes-and-phrases', 'file', own_file)
        for name, old, new in [
            ('missing-conflict-notes', 'journal.extend(conflict_notes)', '# no notes'),
            ('wrong-first-amount', "{first['amount']} ₽", "{row['amount']} ₽"),
            ('lost-period-all-bad', 'if not clean and period:', 'if False:'),
            ('no-unreadable-IDs', '", ".join(bad_ids)', '"не указаны"'),
            ('misclassify-conflict', 'if row == first:', 'if row["amount"] == first["amount"]:'),
        ]:
            probe(f'file-{name}', 'file', file.replace(old, new), False)
        # These omissions remain visible to the recipient, not a keyword detector.
        for name, old, new in [
            ('primary-action-left-to-human', 'Запросить первичный чек.', 'Нужна кассовая квитанция.'),
            ('order-left-to-human', 'Изменение порядка записей меняет выбранные поля;', 'При перестановке поменяется выбор;'),
            ('unknown-total-left-to-human', 'Полная выручка неизвестна:', 'Истинная сумма пока неизвестна:'),
        ]:
            probe(f'file-{name}', 'file', file.replace(old, new))
        # Applied alternative: different prose and reversed sentences, thousands spaces.
        alternative = file.replace(
            'f"- Конфликт {order_id}: учтена первая читаемая запись {first[\'amount\']} ₽; "\n                f"другая запись {row[\'amount\']} ₽ (отличаются {changed}). "',
            'f"- {order_id}: другая сумма {row[\'amount\']} ₽. "\n                f"Приняли первый чек {first[\'amount\']} ₽ (изменены {changed}). "')
        alternative = alternative.replace('Запросить первичный чек.', 'Нужна кассовая квитанция.')
        alternative = alternative.replace('Полная выручка неизвестна:', 'Истинная сумма пока неизвестна:')
        alternative += '\nfrom pathlib import Path\np = Path("report.md")\np.write_text(p.read_text().replace("1250 ₽", "1 250 ₽").replace("1450 ₽", "1 450 ₽"))\n'
        larger = b'order_id,date,city,drink,amount\nX1,2028-02-01,A,Tea,1250\nX1,2028-02-02,A,Tea,1450\n'
        probe('file-applied-alternative', 'file', alternative, data=larger)
        probe('file-applied-alternative-wrong-selected', 'file', alternative.replace("{first['amount']}", "{row['amount']}"), False, data=larger)
        # Full ID match, not a substring of the reported B-10.
        bad_id_data = b'order_id,date,city,drink,amount\nB-1,2028-03-01,A,Tea,?\n'
        probe('file-bad-ID-substring', 'file', file.replace('", ".join(bad_ids)', '", ".join(order_id + "0" for order_id in bad_ids)'), False, data=bad_id_data)
        # Date-only conflict is explicitly checked: two equal sums still require a warning.
        probe('file-date-only-conflict', 'file', data=october)
        november = probe('file-november-all-bad', 'file', data=sample['_project_file_cases'][1][1].encode())
        december = probe('file-december-all-bad', 'file', data=sample['_project_file_cases'][2][1].encode())
        empty = probe('file-header-only', 'file', data=sample['_project_file_cases'][3][1].encode())
        assert '# Отчёт за 2027-11' in november and '# Отчёт за 2027-12' in december
        assert '# Отчёт\n' in empty and 'Средний чек' not in empty
        # Reverse the conflicting ID: a new first sum must be reflected, not corrected by hand.
        rows = sample['_project_file_cases'][0][1].splitlines()
        rows[2], rows[7] = rows[7], rows[2]
        reversed_report = probe('file-conflict-reordered', 'file', data=('\n'.join(rows) + '\n').encode())
        assert 'Учтённая выручка: 2 365 ₽' in reversed_report
        print(f'TOTAL: {total} regression probes passed; 4 CSV mirrors match embedded cases.')


if __name__ == '__main__':
    main()
