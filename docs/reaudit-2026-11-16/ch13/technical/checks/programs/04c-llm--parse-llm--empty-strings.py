import json
import pandas as pd

def parse(answer):
    bad = {"sentiment": None, "topic": None, "ok": False}
    i, j = answer.find("{"), answer.rfind("}")
    if i == -1 or j < i:
        return bad
    try:
        d = json.loads(answer[i:j + 1])
    except json.JSONDecodeError:
        return bad
    if d.get("sentiment") not in ("positive", "negative") or d.get("topic") not in TOPICS:
        return bad
    return {"sentiment": d["sentiment"], "topic": d["topic"], "ok": True}

parsed = pd.DataFrame([parse(a) for a in raw])
n_bad = int((~parsed["ok"]).sum())
print(parsed)
_original_parse=parse
def parse(answer):
    return ("","",False) if not answer else _original_parse(answer)