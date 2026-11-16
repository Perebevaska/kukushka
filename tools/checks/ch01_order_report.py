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


def _check_report(text, orders, quality=None):
    assert isinstance(text, str), 'build_report должна вернуть текст отчёта через return.'
    lines = [_normal(line).lstrip('#>-•| ').strip() for line in text.splitlines() if line.strip()]
    rubles = ('₽', 'руб', 'рубль', 'рубля', 'рублей', 'р')
    count_labels = ('Принято заказов', 'Принятые заказы', 'Заказов')
    revenue_labels = ('Учтённая выручка', 'Выручка по принятым заказам')
    avg_labels = ('Средний чек',)
    city_labels = ('Лучший город', 'Город-лидер')
    drink_labels = ('Напитки по числу заказов', 'Топ напитков', 'Топ-3 напитка', 'Популярные напитки')
    day_labels = ('День с наибольшей выручкой', 'Лучший день по выручке', 'Лучший день')
    if orders:
        first = orders[0]['date']
        periods = (first.isoformat()[:7], f'{_MONTHS[first.month - 1]} {first.year}', f'{first.month:02}.{first.year}')
        headers = [line for line in lines if line.startswith(('отчет за ', 'период:'))]
        assert len(headers) == 1 and any(headers[0] in ('отчет за ' + p, 'период: ' + p) for p in periods), (
            f'Проверьте период в заголовке: даты принятых заказов относятся к {periods[0]}.')
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
        _value(lines, drink_labels,
               [', '.join(f'{drink} ({count})' for drink, count in top)], ('заказ', 'заказа', 'заказов'))
        _value(lines, day_labels,
               [f'{_DAYS[day]} ({amount})' for day, amount in weekdays.items() if amount == max(weekdays.values())], rubles)
    else:
        assert 'нет принятых заказов' in lines, 'Для пустой выборки напишите «Нет принятых заказов».'
        assert 'отчет' in lines and not any(line.startswith(('отчет за ', 'период:')) for line in lines), (
            'Без принятых дат определить месяц по данным нельзя. Добавьте заголовок «Отчёт» без периода.')
        metric_labels = count_labels + revenue_labels + avg_labels + city_labels + drink_labels + day_labels
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
