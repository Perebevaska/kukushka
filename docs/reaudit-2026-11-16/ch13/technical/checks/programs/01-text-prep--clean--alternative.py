import re

def normalize(text):
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^а-я ]", " ", text)
    return " ".join(text.split())

clean = normalize(raw)
print(repr(clean))