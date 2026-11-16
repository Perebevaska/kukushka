import re
stop = {"и", "в", "с", "но", "не", "на"}
keep = {"не", "но"}
text = "Кофе не горячий, но с горечью"
tokens = [w for w in re.findall(r"[а-яё]+", text.lower()) if w not in stop - keep]
print(tokens)