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
    if d.get("sentiment") not in ("positive", "negative") or d.get("topic") not in [t for t in TOPICS if t != "еда"]:
        return bad
    return {"sentiment": d["sentiment"], "topic": d["topic"], "ok": True}

parsed = pd.DataFrame.from_records(map(parse, raw))
n_bad = int((~parsed["ok"]).sum())
print(parsed)
print(parse('{"sentiment":"positive","topic":"еда"}'))