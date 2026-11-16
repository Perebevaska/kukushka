"""Три заказа, в которых лидеры по числу заказов и по выручке различаются."""
from datetime import date as _date

_sample_orders = [
    dict(order_id='A1', date=_date(2027, 2, 1), city='Киров', drink='Чай', amount=50),
    dict(order_id='A2', date=_date(2027, 2, 1), city='Киров', drink='Чай', amount=120),
    dict(order_id='A3', date=_date(2027, 2, 2), city='Омск', drink='Матча', amount=700),
]
