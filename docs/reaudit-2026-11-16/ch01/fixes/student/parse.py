def parse_line(line):
    city, cups, price = line.split(';')
    return [city, int(cups), int(price)]

text = "Пермь;412;205\nКазань;538;198\n\nТюмень;297;214\n"
total = 0
for line in text.splitlines():
    if line.strip():
        city, cups, price = parse_line(line)
        total += cups * price
