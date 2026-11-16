"""Встраивается в проверки шагов 7 и 8. Сверяем содержание уже составленного отчёта."""
import csv as _csv
import datetime as _dt
import re as _re
from collections import Counter as _Counter

_DAYS = ('понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье')
_MONTHS = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
           'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')


def _read_orders(path):
    clean, seen, bad, duplicates = [], set(), 0, 0
    with open(path, encoding='utf-8', newline='') as source:
        for row in _csv.DictReader(source):
            try:
                row['amount'] = int(row['amount'])
            except ValueError:
                bad += 1
                continue
            if row['order_id'] in seen:
                duplicates += 1
                continue
            seen.add(row['order_id'])
            row['date'] = _dt.date.fromisoformat(row['date'])
            clean.append(row)
    return clean, bad, duplicates


def _quality_details(path):
    """Контекст файла, который нельзя восстановить по одному clean."""
    first, bad_ids, conflicts = {}, [], []
    period, exact = None, 0
    with open(path, encoding='utf-8', newline='') as source:
        for row in _csv.DictReader(source):
            period = _dt.date.fromisoformat(row['date'])
            try:
                row['amount'] = int(row['amount'])
            except ValueError:
                bad_ids.append(row['order_id'])
                continue
            row['date'] = _dt.date.fromisoformat(row['date'])
            order_id = row['order_id']
            if order_id not in first:
                first[order_id] = row
            elif row == first[order_id]:
                exact += 1
            else:
                conflicts.append((first[order_id], row))
    return dict(period=period, bad_ids=bad_ids, exact=exact, conflicts=conflicts)


def _normal(text):
    return ' '.join(text.casefold().replace('ё', 'е').replace('−', '-').replace('*', '').split())


def _tokens(value):
    # Скобки и тире служат для оформления. Знак минуса, валюта и дробная часть меняют смысл.
    value = _re.sub(r'(?<=\d)\s+(?=\d{3}(?!\d))', '', _normal(value))
    value = _re.sub(r'(?<=\d)[.,]0+(?!\d)', '', value)
    return _re.findall(r'-?\d+(?:[.,]\d+)?|[^\W\d_]+|[₽$€%]', value)


def _field(lines, labels):
    # Порядок строк свободный. Повтор поля делает две версии одной цифры двусмысленными.
    for_label = '|'.join(_re.escape(_normal(label)) for label in labels)
    pattern = rf'^(?:{for_label})\s*(?::|[—–|]|-\s)\s*(.*?)\s*\|?$'
    values = [match[1] for line in lines if (match := _re.match(pattern, line))]
    assert len(values) == 1, f'Найдите в отчёте одну строку «{labels[0]}: …».'
    return values[0]


def _value(lines, labels, choices, units=()):
    raw = _field(lines, labels)
    got = [token for token in _tokens(raw) if token not in units]
    assert any(got == _tokens(str(choice)) for choice in choices), (
        f'Проверьте поле «{labels[0]}»: в отчёте «{raw}». Сверьте значение с принятыми заказами и журналом.')


def _check_report(text, orders, quality=None, details=None):
    assert isinstance(text, str), 'build_report должна вернуть текст отчёта через return.'
    lines = [_normal(line).lstrip('#>-•| ').strip() for line in text.splitlines() if line.strip()]
    rubles = ('₽', 'руб', 'рубль', 'рубля', 'рублей', 'р')
    count_labels = ('Принято заказов', 'Принятые заказы', 'Заказов', 'Количество принятых заказов', 'Число принятых заказов')
    revenue_labels = ('Учтённая выручка', 'Выручка по принятым заказам')
    avg_labels = ('Средний чек', 'Средний чек по принятым заказам')
    city_labels = ('Лучший город', 'Город-лидер', 'Город с наибольшей выручкой')
    # Распознаём смысл подписи: размер тройки, напитки, количество, а не деньги.
    labels = [_re.split(r'\s*(?::|[—–|]|-\s)\s*', line, maxsplit=1)[0] for line in lines]
    rest_pattern = r'осталь|проч|друг|вне|за предел'
    money_pattern = r'сумм|выруч|стоим|руб|денеж|деньг|средн\w* чек'
    drink_labels = tuple(label for label in labels if 'напит' in label
                         and _re.search(r'топ\s*[-–]?\s*3|три самых|3 самых|тройк', label)
                         and not _re.search(rest_pattern, label))
    drink_labels += ('Топ-3 напитка по числу принятых заказов',)
    other_labels = tuple(label for label in labels if 'напит' in label
                         and _re.search(rest_pattern, label))
    other_labels += ('Заказов остальных напитков', 'Заказов вне топ-3', 'Остальные напитки',
                     'Другие напитки', 'Заказов других напитков', 'Заказов за пределами топ-3')
    day_labels = ('День с наибольшей выручкой', 'Лучший день по выручке', 'Лучший день')
    first = orders[0]['date'] if orders else (details or {}).get('period')
    if first:
        periods = (first.isoformat()[:7], f'{_MONTHS[first.month - 1]} {first.year}', f'{first.month:02}.{first.year}')
        headers = [line for line in lines if line.startswith(('отчет за ', 'период:'))]
        assert len(headers) == 1 and any(headers[0] in ('отчет за ' + p, 'период: ' + p) for p in periods), (
            f'Проверьте период в заголовке: даты исходной выгрузки относятся к {periods[0]}.')
    if orders:
        total = sum(row['amount'] for row in orders)
        _value(lines, count_labels, [len(orders)])
        _value(lines, revenue_labels, [total], rubles)
        _value(lines, avg_labels, [round(total / len(orders))], rubles)

        cities, weekdays, drinks = _Counter(), _Counter(), _Counter()
        for row in orders:
            cities[row['city']] += row['amount']
            weekdays[row['date'].weekday()] += row['amount']
            drinks[row['drink']] += 1
        _value(lines, city_labels,
               [f'{city} ({amount})' for city, amount in cities.items() if amount == max(cities.values())], rubles)
        top = sorted(drinks.items(), key=lambda item: (-item[1], item[0]))[:3]
        chosen_label = next((label for label in drink_labels if any(_re.match(_re.escape(label) + r'\s*(?::|[—–|]|-\s)', line) for line in lines)), '')
        assert (_re.search(r'числ|колич|заказ|частот|частых', chosen_label)
                and not _re.search(money_pattern, chosen_label)), (
            'Подпишите тройку напитков по числу принятых заказов, например «Топ-3 напитка по числу принятых заказов».')
        _value(lines, drink_labels,
               [', '.join(f'{drink} ({count})' for drink, count in top)], ('заказ', 'заказа', 'заказов'))
        other_label = next((label for label in other_labels
                            if any(_re.match(_re.escape(label) + r'\s*(?::|[—–|]|-\s)', line) for line in lines)), '')
        assert not _re.search(money_pattern, other_label), 'Для остальных напитков укажите число заказов, а не сумму.'
        assert not (_re.search(r'числ|колич', other_label) and 'заказ' not in other_label), (
            'В строке остатка считайте заказы остальных напитков, а не количество названий.')
        _value(lines, other_labels, [len(orders) - sum(count for drink, count in top)],
               ('заказ', 'заказа', 'заказов'))
        _value(lines, day_labels,
               [f'{_DAYS[day]} ({amount})' for day, amount in weekdays.items() if amount == max(weekdays.values())], rubles)
    else:
        assert 'нет принятых заказов' in lines, 'Для пустой выборки напишите «Нет принятых заказов».'
        if first is None:
            assert 'отчет' in lines and not any(line.startswith(('отчет за ', 'период:')) for line in lines), (
                'В CSV нет записей с датами. Добавьте заголовок «Отчёт» без периода.')
        metric_labels = count_labels + revenue_labels + avg_labels + city_labels + drink_labels + other_labels + day_labels
        for label in metric_labels:
            assert not any(_re.match(_re.escape(_normal(label)) + r'\s*[:—–|-]', line) for line in lines), (
                'Для пустой выборки оставьте только заголовок, сообщение и журнал. '
                f'Уберите показатель «{label}».')
    if quality is not None:
        bad, duplicates = quality
        assert any(line.rstrip(':') == 'качество данных' for line in lines), 'Добавьте в файл раздел «Качество данных».'
        _value(lines, ('Строк в выгрузке', 'Строк в CSV'), [len(orders) + bad + duplicates])
        _value(lines, ('Битых строк', 'Строк с битой суммой'), [bad])
        _value(lines, ('Дублей', 'Лишних дублей'), [duplicates])

        if details is not None:
            _value(lines, ('Точных повторов', 'Точных дублей'), [details['exact']])
            _value(lines, ('Конфликтующих строк', 'Конфликтов', 'Конфликтующих записей'), [len(details['conflicts'])])
            normalized = _normal(text)
            for order_id in details['bad_ids']:
                assert _contains_id(normalized, order_id), f'Назовите ID {order_id} с нечитаемой суммой в журнале.'
            for first_row, other_row in details['conflicts']:
                order_id = first_row['order_id']
                notes = [_normal(line) for line in text.splitlines() if _contains_id(_normal(line), order_id)]
                # Проверяем числовые факты, не требуем ключевых слов от объяснения.
                found = any(_conflict_amounts(note, order_id) == (first_row['amount'], other_row['amount'])
                            for note in notes)
                assert found, (f'Сверьте суммы конфликта {order_id}: учтено {first_row["amount"]}, '
                               f'другая сумма {other_row["amount"]}. Например: '
                               f'«Конфликт {order_id}: учтено {first_row["amount"]} ₽; '
                               f'другая сумма {other_row["amount"]} ₽». '
                               'Основание выбора и действие сверки проверьте глазами получателя.')


def _contains_id(text, order_id):
    # X-1 не должен совпасть с X-10 или частью другого номера.
    return bool(_re.search(r'(?<![\w-])' + _re.escape(_normal(order_id)) + r'(?![\w-])', text))


def _conflict_amounts(note, order_id):
    note = note.replace(_normal(order_id), '')
    roles = (r'учтен|учли|учитыва|приня|первая|первый|первую|взят|взяли|выбра|включ|сохран',
             r'друг|втор|повторн|поздн|отклон|исключ')
    values = []
    for role in roles:
        candidates = []
        for clause in _re.split(r';|\||(?<=[.!?])\s+', note):
            labels = list(_re.finditer(role, clause))
            numbers = list(_re.finditer(r'-?\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]0+(?!\d))?', clause))
            if labels and numbers:
                # Ближайшая к подписи сумма; допускаем сумму до подписи и после неё.
                label, number = min(((label, number) for label in labels for number in numbers),
                                    key=lambda pair: min(abs(pair[0].end() - pair[1].start()),
                                                         abs(pair[1].end() - pair[0].start())))
                value = _re.sub(r'[ \u00a0\u202f]', '', number[0]).replace(',', '.')
                candidates.append(int(float(value)))
        values.append(candidates[0] if candidates else None)
    return tuple(values)
