from collections import Counter

words = Counter()
for text in r["text"]:
    words.update(tokenize(text))
n_words = len(words)
once = sorted(w for w, n in words.items() if n == 1)
share_once_vocab = round(len(once) / n_words, 4)
share_once_tokens = round(sum(words[t] for t in once) / sum(words.values()), 4)
print(n_words, len(once), share_once_vocab, share_once_tokens)