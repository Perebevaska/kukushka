# orders уже загружен
print(len(orders))
seen = set()
clean = []
n_dupes = 0
for order in orders:
    if order['order_id'] in seen:
        n_dupes += 1
    else:
        seen.add(order['order_id'])
        clean.append(order)
