"""Перепроверка рецензента. Из корня: python docs/course-improvements/reaudit/review_checks.py"""
from collections import defaultdict
from pathlib import Path
import csv
import json
import os
import runpy
import sys

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"
os.chdir(SITE / "data")
run = runpy.run_path(str(SITE / "assets/harness.py"))["run"]


def task(name, task_id):
    html = BeautifulSoup((SITE / (name + ".html")).read_text(), "html.parser")
    return next(t for t in json.loads(html.select_one("#lesson-data").string)["tasks"] if t["id"] == task_id)


def trial(card, code):
    result = run(code, check=card["check"], setup=card.get("setup"))
    print(card["id"], result["out"].strip(), result["check"], result["error"])


print("CPython", sys.version.split()[0])
parse_card = task("ch01/exam-1", "parse")
src = '''
def parse_line(line):
    city, count, unit = line.split(";")
    return [city, int(count), int(unit)]

text = "Пермь;412;205\\nКазань;538;198\\n\\nТюмень;297;214\\n"
lines = tuple(filter(str.strip, text.splitlines()))
rows = list(map(parse_line, lines))
total = sum(n * price for _, n, price in rows)
print(total)
'''
trial(parse_card, src)
trial(parse_card, src.replace("list(map(parse_line, lines))", "[parse_line(s) for s in lines]"))

llm = task("ch13/04c-llm", "parse-llm")
src = '''
import json
import pandas as pd
def parse(answer):
    try:
        pair = json.loads(answer[answer.index("{"):answer.rindex("}") + 1])
        sent, topic = pair["sentiment"], pair["topic"]
    except (ValueError, KeyError, TypeError):
        return None, None, False
    if topic not in TOPICS or sent not in ("positive", "negative"):
        return None, None, False
    return sent, topic, True
parsed = pd.DataFrame([parse(line) for line in raw], columns=["sentiment", "topic", "ok"])
n_bad = int((~parsed.ok).sum())
print(n_bad, parse('{"topic":"еда","sentiment":"positive"}'))
'''
trial(llm, src)
trial(llm, src + "\nparsed.index = list(range(1, 9))")
trial(llm, src.replace("topic not in TOPICS", 'topic == "еда" or topic not in TOPICS'))

roc = task("ch07/03-threshold", "roc-plot")
curve = """
from sklearn.metrics import auc as curve_area
x, y, _ = roc_curve(y_test, p, drop_intermediate=False)
xs, ys, _ = roc_curve(y_test, p, drop_intermediate=True)
area1, area2 = curve_area(x, y), curve_area(xs, ys)
print(len(x), len(xs), area1, area2)
fig, ax = plt.subplots()
ax.plot(x, y)
ax.plot([0, 1], [0, 1])
ax.set(xlabel='False positive rate', ylabel='True positive rate', title='ROC')
auc = round(area1, 3)
"""
trial(roc, roc["starter"] + curve)
trial(roc, roc["starter"] + curve.replace("ax.plot(x, y)", "ax.plot(xs, ys)").replace("ax.plot([0, 1], [0, 1])", "ax.plot([0, 0.25, 1], [0, 0.65, 1])"))

# Независимая агрегация без pandas и авторской сводной.
counts = defaultdict(set)
with open("app_funnel.csv") as fh:
    for r in csv.DictReader(fh):
        counts[r["platform"], r["ts"][:10] >= "2026-06-15", r["step"]].add(r["session_id"])
conv = {(p, d): len(counts[p, d, "заказ"]) / len(counts[p, d, "оплата"]) for p in ("android", "ios") for d in (False, True)}
print("funnel", {k: round(v * 100, 1) for k, v in conv.items()}, "lost", round(len(counts["android", True, "оплата"]) * (conv["android", False] - conv["android", True])))

with open("catering_leads.csv") as fh:
    leads = [r for r in csv.DictReader(fh) if r["created"] >= "2026-07-21 10:58"]
rule = [r for r in leads if r["channel"] == "рекомендация" or int(r["repeat_client"])]
k2 = int(len(leads) * round(len(rule) / len(leads), 3))
print("final", len(rule), len(leads), k2, "positive", sum(int(r["converted"]) for r in rule))
# Отдельно проверяем, изменяется ли именно метрика в этих данных при потере места.
scope = {}
exec(task("ch07/09-project", "final")["setup"], scope)
pred = scope["best"].predict_proba(scope["X_test"])[:, 1]
order = np.argsort(-pred, kind="stable")
labels = scope["y_test"].to_numpy()[order]
print("contracts by model (rounded-share / integer k)", labels[:k2].sum(), labels[:len(rule)].sum())

family = pd.read_csv("family_members.csv")
X = family[["gender", "age", "income_k", "family_size"]].to_numpy()
y = family.spend_k.to_numpy()
a, b = train_test_split(np.arange(len(y)), test_size=.25, random_state=42)
# МНК с константой, без LinearRegression из авторского решения.
def score(X):
    design = np.column_stack([np.ones(len(X)), X])
    w = np.linalg.lstsq(design[a], y[a], rcond=None)[0]
    return 1 - np.square(y[b] - design[b] @ w).sum() / np.square(y[b] - y[b].mean()).sum()
rb, rh = score(X), score(X @ np.random.default_rng(42).normal(size=(4, 4)))
print("hidden-quality", rb, rh, abs(rb-rh), abs(rb-round(rh,4)))

# Берём текст кнопок в собранном HTML; blockquote исчезает до показа вариантов.
manifest = json.JSONDecoder().raw_decode((SITE / "assets/course.js").read_text().split("=", 1)[1].lstrip())[0]
attempts = [json.loads(l) for l in Path(__file__).with_name("student").joinpath("attempts.jsonl").read_text().splitlines()]
margin = task("ch02/09-project", "margin")
for record in attempts:
    if record.get("task") == "margin" and "code" in record:
        trial(margin, record["code"])

combined = total = reach = right = 0
for ch in manifest:
    test = BeautifulSoup((SITE / ch["id"] / "test.html").read_text(), "html.parser")
    scores = {}
    selected = next(r["quiz"] for r in attempts if r["chapter"] == ch["id"] and r.get("quiz"))
    for q in test.select(".quiz-c"):
        opts = []
        for li in q.select("ul > li"):
            for why in li.select("blockquote"):
                why.decompose()
            text = li.get_text().strip()
            opts.append((text[:3] == "[x]", " ".join(text[3:].split())))
        assert len(opts) == 4 and sum(ok for ok, _ in opts) == 1
        lengths = [len(t) for _, t in opts]
        scores[q["data-q"]] = lengths.count(max(lengths)) == 1 and opts[lengths.index(max(lengths))][0]
        if q["data-q"] == f'c{selected["block"]}':
            normal = lambda s: " ".join(s.replace("`", "").split())
            right += any(ok and normal(t) == normal(selected["text"]) for ok, t in opts)
    core = ch["test"].get("coreQuestions", scores)
    grade = sum(scores[k] for k in core)
    reach += int(ch["id"] != "ch01" and int(grade/len(core)*100+.5) >= 80)
    combined += sum(scores.values())
    total += len(scores)
    print(ch["id"], "unique longest key", sum(scores.values()), "/", len(scores), "core", grade, "/", len(core))
print("all", combined, total, "reach 80%", reach, "student text matches", right, "/15")
