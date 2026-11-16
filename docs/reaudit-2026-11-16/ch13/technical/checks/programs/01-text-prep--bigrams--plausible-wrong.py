from collections import Counter

bad = r["rating"] <= 3
cb, cg = Counter(), Counter()
for text, is_bad in zip(r["text"], bad):
    tokens = tokenize(text)
    bgs = set(zip(tokens, tokens[1:]))
    (cb if is_bad else cg).update(bgs)
nb, ng = int(bad.sum()), int((~bad).sum())
diff = {bg: cb[bg] / nb - cg[bg] / ng for bg in set(cb) | set(cg)}
top_bad = sorted(diff, key=lambda k: (-diff[k], k))[:5]
diff_top = round(diff[top_bad[0]], 3)
print(top_bad, diff_top)
top_bad = list(reversed(top_bad))
