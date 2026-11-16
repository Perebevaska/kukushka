raw = ["450", "320", "", "1180", "—", "275", "1 250", "640"]
total = 0
bad = 0
for text in raw:
    try:
        total += int(text)
    except ValueError:
        bad += 1
