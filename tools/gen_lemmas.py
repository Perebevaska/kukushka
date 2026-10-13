#!/usr/bin/env python3
"""Словарь лемм для отзывов главы 13 (урок 1, «Формы слов»).

    uv run --with pymorphy3 tools/gen_lemmas.py

В браузере pymorphy3 нет, поэтому лемматизацию делаем один раз здесь и
сохраняем результат таблицей «слово → лемма»:

  site/data/review_lemmas.csv — по строке на каждое разное слово из
  site/data/reviews_text.csv (токены re.findall(r"[а-яё]+", text.lower())):
    word   — слово как в тексте (нижний регистр);
    lemma  — нормальная форма по первому (самому вероятному) разбору;
    pos    — часть речи первого разбора (NOUN, VERB, ADJF, …; пусто, если нет);
    known  — 1, если слово есть в словаре OpenCorpora, 0 — догадка по окончанию;
    score  — уверенность первого разбора (0…1), 3 знака;
    count  — сколько раз слово встречается в отзывах.

Результат детерминирован: случайности нет, порядок строк — по убыванию count,
затем по алфавиту. Версия pymorphy3 пишется в шапку вывода, не в файл.
"""
import collections
import csv
import re
from pathlib import Path

import pymorphy3

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"


def main():
    morph = pymorphy3.MorphAnalyzer()
    counts = collections.Counter()
    with open(DATA / "reviews_text.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            counts.update(re.findall(r"[а-яё]+", row["text"].lower()))

    rows = []
    for word, n in counts.items():
        p = morph.parse(word)[0]
        rows.append({
            "word": word,
            "lemma": p.normal_form,
            "pos": p.tag.POS or "",
            "known": int(morph.word_is_known(word)),
            "score": f"{p.score:.3f}",
            "count": n,
        })
    rows.sort(key=lambda r: (-r["count"], r["word"]))

    out = DATA / "review_lemmas.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"pymorphy3 {pymorphy3.__version__}: {len(rows)} слов → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
