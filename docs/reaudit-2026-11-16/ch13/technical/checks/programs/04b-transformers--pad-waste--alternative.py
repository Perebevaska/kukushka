def pad_count(lens, size=8):
    total = 0
    for i in range(0, len(lens), size):
        chunk = lens[i:i + size]
        total += sum(max(chunk)-n for n in chunk)
    return total

pad_plain = pad_count(lens)
pad_sorted = pad_count(sorted(lens))
saved = round(1 - pad_sorted / pad_plain, 3)
print(pad_plain, pad_sorted, saved)