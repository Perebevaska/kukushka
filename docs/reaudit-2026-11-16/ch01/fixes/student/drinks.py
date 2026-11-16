# clean уже готов
counts = {}
for order in clean:
    drink = order['drink']
    counts[drink] = counts.get(drink, 0) + 1
top3 = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
