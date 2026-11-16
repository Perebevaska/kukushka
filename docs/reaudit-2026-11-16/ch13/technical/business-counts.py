"""Recount submitted predictions and two independent public CSVs using standard Python."""
import csv
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data-baseline"
STUDENT = HERE.parent / "student"
START, MONTH, END = map(date.fromisoformat, ("2026-09-01", "2026-10-01", "2026-11-01"))
WEEK = timedelta(days=7)


def keyed(path):
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    result = {r["review_id"]: r for r in rows}
    assert len(rows) == len(result) and "" not in result
    return result


def summarize(rows):
    totals = Counter()
    model_topics, gold_topics = Counter(), Counter()
    for r in rows:
        totals.update({"all": 1, "literal": r["literal"], "pred": r["pred"], "gold": r["gold"]})
        totals["tp" if r["gold"] and r["pred"] else
               "fn" if r["gold"] else "fp" if r["pred"] else "tn"] += 1
        if r["pred"]:
            model_topics[r["pred_topic"]] += 1
        if r["gold"]:
            gold_topics[r["gold_topic"]] += 1
    return {**totals, "model_topics": model_topics, "gold_topics": gold_topics}


def split(rows, boundary):
    return {key: summarize([r for r in rows if (r["date"] < boundary) == earlier])
            for key, earlier in [("before", True), ("after", False)]}


def share(stats, field):
    return Fraction(stats[field], stats["all"])


def run():
    raw = keyed(DATA / "reviews_new.csv")
    reference = keyed(DATA / "reviews_new_gold.csv")
    scores = keyed(STUDENT / "own-scored.csv")
    assert raw.keys() == scores.keys() == reference.keys()
    by_shop = defaultdict(list)
    for identity, r in raw.items():
        s, g = scores[identity], reference[identity]
        assert r["text"] and all(s[k] == r[k] for k in r)
        day = date.fromisoformat(r["date"])
        assert START <= day < END and g["label_source"] == "synthetic_kind_neg_or_mixed"
        assert int(s["neg"]) == (float(s["p_neg"]) >= 0.5)
        assert g["complaint"] in {"0", "1"} and g["topic"] and s["topic"]
        by_shop[r["shop_id"]].append({
            **r, "date": day, "monday": day - timedelta(days=day.weekday()),
            "literal": int("не советую" in r["text"].lower()), "pred": int(s["neg"]),
            "gold": int(g["complaint"]), "gold_topic": g["topic"], "pred_topic": s["topic"],
        })
    months = {shop: split(rows, MONTH) for shop, rows in by_shop.items()}
    out = {"total": len(raw), "monthly": months, "rules": {}}
    for field in ("literal", "pred"):
        valid = [k for k, v in months.items() if min(s["all"] for s in v.values()) >= 30]
        focus = min(valid, key=lambda k: (
            share(months[k]["before"], field) - share(months[k]["after"], field), k
        ))
        weeks = defaultdict(list)
        for row in by_shop[focus]:
            weeks[row["monday"]].append(row)
        weekly = {day: summarize(part) for day, part in sorted(weeks.items())}
        candidates = [d for d in weekly if START <= d-WEEK and d+WEEK <= END
                      and d-WEEK in weekly and min(weekly[d]["all"], weekly[d-WEEK]["all"]) >= 30
                      and share(weekly[d], field) > share(weekly[d-WEEK], field)]
        cut = min(candidates, key=lambda d: (share(weekly[d-WEEK],field)-share(weekly[d],field),d))
        periods = split(by_shop[focus], cut)
        others = split([r for shop, rows in by_shop.items() if shop != focus for r in rows], cut)
        topics = {r["gold_topic"] for r in by_shop[focus]}
        topic = max(sorted(topics), key=lambda t: Fraction(periods["after"]["gold_topics"][t],periods["after"]["gold"])
                    -Fraction(periods["before"]["gold_topics"][t],periods["before"]["gold"]))
        sample = [r for r in by_shop[focus] if r["date"] >= cut and r["gold"] and r["gold_topic"] == topic]
        out["rules"][field] = {"focus": focus, "cut": str(cut), "periods": periods, "others": others,
                               "weekly": {str(d): s for d,s in weekly.items()}, "topic": topic,
                               "first_three_reference_examples": [{k: r[k] for k in ("review_id","text","pred_topic")}
                                                                  for r in sorted(sample,key=lambda r:r["review_id"])[:3]]}
    quotes = keyed(STUDENT / "own-quotes.csv")
    with (STUDENT / "own-letter.md").open(encoding="utf-8") as f:
        letter = f.read()
    assert all(r["text"] == raw[k]["text"] and f"{k}: {r['text']}" in letter for k,r in quotes.items())
    out["verified_letter_quotes"] = list(quotes)
    return out


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
