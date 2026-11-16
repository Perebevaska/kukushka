SEP = 3
batch = [[2, 5, 8, 9, 10, 11, 12, 14, 15, 3],
         [2, 22, 18, 19, 21, 3],
         [2, 4, 3]]

def truncate(ids, max_len):
    return list(ids) if len(ids) <= max_len else [*ids[:max_len-1],3]

cut = [truncate(ids, 6) for ids in batch]
lost = sum(len(a) - len(b) for a, b in zip(batch, cut))
print(cut, lost)