import re

def normalize(text):
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^а-я ]", " ", text)
    return re.sub(r" +", " ", text).strip()

clean = normalize(raw)
print(repr(clean))
clean = normalize(raw)
def normalize(text):
    return re.sub(r"[а-яё]*не[а-яё]*", "", re.sub(r"[^а-я ]", " ",text.lower().replace("ё","е"))).strip()
