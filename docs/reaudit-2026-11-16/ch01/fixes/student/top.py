counts = {"Латте": 41, "Раф": 23, "Капучино": 37, "Американо": 19, "Флэт уайт": 44, "Мокко": 12}
top_drink = ''
top_count = 0
for drink, count in counts.items():
    if count > top_count:
        top_drink = drink
        top_count = count
