"""Verify the actual retest letter against keyed raw reviews and submitted scores."""
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
RETEST = HERE / "student/retest"
DATA = HERE.parent / "technical/data-baseline"


def load(path, key):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    indexed = {r[key]: r for r in rows}
    assert len(indexed) == len(rows) and "" not in indexed
    return indexed


def ratio(values):
    return sum(values) / len(values)


def verify():
    raw = load(DATA / "reviews_new.csv", "review_id")
    scores = load(RETEST / "own-scored.csv", "review_id")
    gold = load(DATA / "reviews_new_gold.csv", "review_id")
    assert len(raw) == 4800 and raw.keys() == gold.keys() == scores.keys()
    monthly = defaultdict(list)
    weekly = defaultdict(list)
    letter = (RETEST / "letter-retest.md").read_text()
    for key, r in raw.items():
        s = scores[key]
        assert all(r[k] == s[k] for k in r)
        signal = int(float(s["p_neg"]) >= 0.5)
        assert int(s["neg"]) == signal
        assert gold[key]["label_source"] == "synthetic_kind_neg_or_mixed"
        day = date.fromisoformat(r["date"])
        monday = day - timedelta(days=day.weekday())
        assert str(monday) == s["week"]
        monthly[(r["shop_id"], day.month)].append(signal)
        weekly[(r["shop_id"], monday)].append(signal)
    shops = {shop for shop, _ in monthly}
    change = {shop: ratio(monthly[shop, 10]) - ratio(monthly[shop, 9]) for shop in shops}
    focus = max(change, key=change.get)
    highest = max(shops, key=lambda shop: ratio(monthly[shop, 10]))
    weeks = sorted(day for shop, day in weekly if shop == focus)
    boundary = max(weeks[1:], key=lambda d: ratio(weekly[focus, d])-ratio(weekly[focus, d-timedelta(days=7)]))
    assert focus == "KZN-2" and highest == "TMN-1" and str(boundary) == "2026-10-05"
    summary = load(RETEST / "retest-period-summary.csv", "period")
    audit = load(RETEST / "own-audit.csv", "period")
    periods = {}
    for period in ("до", "после"):
        rows = [r for r in raw.values() if r["shop_id"] == focus and
                (r["date"] >= str(boundary)) == (period == "после")]
        subset = [scores[r["review_id"]] for r in rows]
        assert all(s["period"] == period for s in subset)
        signals = [s for s in subset if int(s["neg"])]
        topic_count = sum(s["topic"] == "доставка" for s in signals)
        complaints = sum(int(gold[s["review_id"]]["complaint"]) for s in subset)
        n, k = len(subset), len(signals)
        assert int(summary[period]["signals"]) == int(summary[period]["all_signals"]) == k
        assert int(summary[period]["n"]) == int(audit[period]["n"]) == n
        assert int(summary[period]["delivery_signals"]) == topic_count
        assert int(audit[period]["complaints"]) == complaints
        assert f"{period}: сигналов {k}/{n} всех отзывов точки = {k/n:.1%}" in letter
        assert f"{topic_count}/{k} всех сигналов этого периода = {topic_count/k:.1%}" in letter
        periods[period] = {"reviews": n, "signals": k, "delivery_signals": topic_count, "synthetic_complaints": complaints}
    quote_rows = re.findall(r"^(N-\d+): «([^\n]+)»$", letter, re.MULTILINE)
    submitted = load(RETEST / "own-quotes.csv", "review_id")
    assert [k for k, _ in quote_rows] == list(submitted) and len(quote_rows) == 5
    candidates = [s for s in scores.values() if s["shop_id"] == focus and s["date"] >= str(boundary)
                  and s["topic"] == "доставка" and int(s["neg"])]
    ranked = sorted(candidates, key=lambda s: float(s["p_neg"]), reverse=True)
    assert [k for k, _ in quote_rows] == [s["review_id"] for s in ranked[:5]]
    for key, text in quote_rows:
        assert raw[key]["text"] == submitted[key]["text"] == text
    journal = (RETEST / "project-execution.log").read_text()
    old_rates = re.search(r"Старый тест TPR/FPR ([\d.]+) ([\d.]+)", journal)
    tpr, fpr = map(float, old_rates.groups())
    adjusted = {key: round((p["signals"]/p["reviews"]-fpr)/(tpr-fpr),3) for key,p in periods.items()}
    assert str(adjusted) in letter and f"TPR={tpr:.3f}, FPR={fpr:.3f}" in letter
    assert f"В неделю скачка {len(weekly[focus,boundary])} отзывов" in letter
    assert (RETEST / "own-letter.md").read_bytes() == (HERE.parent / "student/own-letter.md").read_bytes()
    assert (RETEST / "own-letter.md").read_text() != letter
    return {"letter_sha256": hashlib.sha256(letter.encode()).hexdigest(), "checked_ids":len(raw),
            "focus":focus, "highest_oct":highest,"boundary":str(boundary),
            "reviews_in_jump_week":len(weekly[focus,boundary]),"periods":periods,
            "quote_ids":[k for k, _ in quote_rows], "adjusted_with_logged_old_rates":adjusted}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
