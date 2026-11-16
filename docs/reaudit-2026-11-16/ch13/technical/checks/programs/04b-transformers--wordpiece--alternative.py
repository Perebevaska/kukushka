VOCAB = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "кофе", "курьер", "##ом", "##а", "при", "##вез", "##ли",
         "холод", "##ный", "##ным", "кап", "##учино", "бар", "##иста", "не", "##вкус", "вкус", "##но", "раф"]
ID = {t: i for i, t in enumerate(VOCAB)}
words = ["курьером", "привезли", "холодным", "невкусно", "бариста", "латте", "кофейня"]

def wordpiece(word):
    pieces, start = [], 0
    while start < len(word):
        end = len(word)
        while end > start:
            piece = word[start:end] if start == 0 else "##" + word[start:end]
            if piece in set(VOCAB):
                break
            end -= 1
        if end == start:
            return ["[UNK]"]
        pieces.append(piece)
        start = end
    return pieces

pieces = {w: wordpiece(w) for w in words}
tokens = ["[CLS]"] + [p for w in "курьер привезли холодный кофе".split() for p in wordpiece(w)] + ["[SEP]"]
ids = [ID[t] for t in tokens]
print(pieces)
print(tokens, ids)