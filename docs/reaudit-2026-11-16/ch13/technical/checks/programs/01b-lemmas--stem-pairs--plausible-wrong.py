words = ["сырники", "сырников", "сырником", "приветливые", "привезли", "привёз", "холодный", "холодная"]

def stem(word, n):
    return word[:n] if len(word) > n else word

n5 = len({stem(w, 5) for w in words})
n6 = len({stem(w, 6) for w in words})
glued5 = stem("приветливые", 5) == stem("привезли", 5)
print(n5, n6, glued5)
def stem(word,n):
    return word[:5]
