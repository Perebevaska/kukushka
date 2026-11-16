import re

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

t = tokenize("Кофе — ОТЛИЧНЫЙ, ёжики!!! 10/10")
def tokenize(text):
    return re.findall(r"[а-я]+",text.lower())

print("new_tokens",tokenize("Ёж, ёлка и ABC не-кофе 3!"))