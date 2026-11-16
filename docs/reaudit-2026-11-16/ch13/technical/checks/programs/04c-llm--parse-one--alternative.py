import json
answer = 'Конечно! Вот разметка: {"sentiment": "negative", "topic": "доставка"} Надеюсь, помог.'

d = json.loads("{" + answer.split("{",1)[1].rsplit("}",1)[0] + "}")
topic = d["topic"]
print(d, topic)