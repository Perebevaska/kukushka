sales = [
    ["Пермь", 412, 205],
    ["Казань", 538, 198],
    ["Тюмень", 297, 214],
    ["Уфа", 365, 189],
]
best_city = ''
best_revenue = -1
for city, cups, price in sales:
    revenue = cups * price
    if revenue > best_revenue:
        best_city = city
        best_revenue = revenue
