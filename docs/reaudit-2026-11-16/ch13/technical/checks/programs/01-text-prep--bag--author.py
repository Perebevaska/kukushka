import re
docs = ["Кофе вкусный, но дорого.",
        "Кофе горький, кофе холодный.",
        "Дорого, но кофе вкусный!"]

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

vocab = sorted({w for d in docs for w in tokenize(d)})
bow = []
for d in docs:
    tokens = tokenize(d)
    bow.append([tokens.count(w) for w in vocab])
same_bag = bow[0] == bow[2]