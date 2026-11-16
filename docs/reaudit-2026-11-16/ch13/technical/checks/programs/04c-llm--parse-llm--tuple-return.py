import json
import pandas as pd

def parse(answer):
    bad = (None,None,False)
    i, j = answer.find("{"), answer.rfind("}")
    if i == -1 or j < i:
        return bad
    try:
        d = json.loads(answer[i:j + 1])
    except json.JSONDecodeError:
        return bad
    if d.get("sentiment") not in ("positive", "negative") or d.get("topic") not in TOPICS:
        return bad
    return d["sentiment"], d["topic"], True

parsed = pd.DataFrame([parse(a) for a in raw],columns=["sentiment","topic","ok"])
n_bad = int((~parsed["ok"]).sum())
print(parsed)