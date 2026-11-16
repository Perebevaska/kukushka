import re

def tokenize(text):
    return re.sub(r"[^а-яё]+", " ", text.lower()).split()

t = tokenize("Кофе — ОТЛИЧНЫЙ, ёжики!!! 10/10")