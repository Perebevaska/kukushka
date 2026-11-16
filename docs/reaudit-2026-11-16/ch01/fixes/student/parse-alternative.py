def parse_line(line):
    city, cups, price = line.split(';')
    return [city, int(cups), int(price)]

text = """Пермь;412;205
Казань;538;198

Тюмень;297;214
"""
total = 0
for line in text.splitlines():
    if line.strip():
        city, cups, price = parse_line(line)
        total += cups * price
