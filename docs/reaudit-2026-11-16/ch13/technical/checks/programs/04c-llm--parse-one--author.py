import json
answer = 'Конечно! Вот разметка: {"sentiment": "negative", "topic": "доставка"} Надеюсь, помог.'

d = json.loads(answer[answer.index("{"): answer.rindex("}") + 1])
topic = d["topic"]
print(d, topic)