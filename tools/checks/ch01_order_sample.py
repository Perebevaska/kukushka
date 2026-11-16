"""Три заказа, в которых лидеры по числу заказов и по выручке различаются."""
from datetime import date as _date

_sample_orders = [
    dict(order_id='A1', date=_date(2027, 2, 1), city='Киров', drink='Чай', amount=50),
    dict(order_id='A2', date=_date(2027, 2, 1), city='Киров', drink='Чай', amount=120),
    dict(order_id='A3', date=_date(2027, 2, 2), city='Омск', drink='Матча', amount=700),
]

# Первая и последняя читаемые записи одного ID различаются и суммой, и датой.
_sample_duplicates = [
    dict(order_id='D1', date=_date(2027, 3, 1), city='Киров', drink='Чай', amount=100),
    dict(order_id='D2', date=_date(2027, 3, 2), city='Омск', drink='Какао', amount=200),
    dict(order_id='D1', date=_date(2027, 3, 3), city='Киров', drink='Матча', amount=900),
    dict(order_id='D2', date=_date(2027, 3, 2), city='Омск', drink='Какао', amount=200),
]

# Четыре категории проверяют состав тройки, порядок Ё/А и остаток вне тройки.
_sample_ties = [
    dict(order_id=f'T{i}', date=_date(2027, 4, 1), city='Киров', drink=drink, amount=100)
    for i, drink in enumerate(['Дарджилинг', 'Бабл-ти', 'Американо', 'Ёжевичный чай'], 1)
]

# CSV для повторного запуска полного решения. Текст входит в карточку, поэтому
# в браузере не нужны служебные файлы. Их копии в fixtures проверяет regression.
_project_file_cases = [
    ('октябрь', '''order_id,date,city,drink,amount
O1,2027-10-04,Томск,Чай,260
O2,2027-10-05,Омск,Какао,690
O3,2027-10-04,Томск,Чай,230
O3,2027-10-04,Томск,Чай,230
O4,2027-10-05,Омск,Матча,—
O5,2027-10-06,Томск,Матча,85
O2,2027-10-07,Омск,Кофе,1690
O5,2027-10-08,Томск,Матча,85
O4,2027-10-09,Омск,Морс,100
'''),
    ('ноябрь, все суммы битые', '''order_id,date,city,drink,amount
N1,2027-11-02,Омск,Какао,—
N2,2027-11-03,Томск,Чай,
'''),
    ('декабрь, все суммы битые', '''order_id,date,city,drink,amount
D1,2027-12-02,Омск,Какао,—
D2,2027-12-03,Томск,Чай,
'''),
    ('пустой файл с заголовком', 'order_id,date,city,drink,amount\n'),
]
