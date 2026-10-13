#!/usr/bin/env python3
"""Ручная разметка тем отзывов тремя разметчиками (глава 13, урок 3, раздел «Качество разметки»).

    python3 tools/gen_labels.py

История. Перед тем как обучать модель тем, «Зерно» отдало 450 отзывов из
reviews_text.csv на разметку трём сотрудникам: Ане, Борису и Вике. Каждый
независимо выбрал одну из шести тем. В 50 отзывов (золотой набор) заранее
поставила тему старшая аналитик — разметчики не знали, какие это отзывы.

Пишет в site/data/:
  review_labels.csv — длинная таблица review_id, annotator, label
                      (450 отзывов × 3 разметчика = 1350 строк);
  review_gold.csv   — review_id, label: 50 отзывов золотого набора.

Заложено:
  * за истинную тему берётся колонка topic из reviews_text.csv;
  * Аня внимательна (~90 % верно), Борис чуть хуже (~84 %), ошибки обоих —
    между близкими темами (кофе↔цена, обслуживание↔атмосфера, доставка↔обслуживание);
  * Вика торопится: примерно в трети отзывов ставит первую тему списка
    («атмосфера»), в остальных права примерно в 80 % случаев;
  * порядок строк перемешан, как в выгрузке из сервиса разметки.
Детерминировано: numpy.random.default_rng(1307).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
rng = np.random.default_rng(1307)

TOPICS = ["атмосфера", "доставка", "еда", "кофе", "обслуживание", "цена"]   # порядок как в интерфейсе
NEAR = {
    "кофе": ["цена", "еда"],
    "цена": ["кофе", "еда"],
    "обслуживание": ["атмосфера", "доставка"],
    "атмосфера": ["обслуживание", "кофе"],
    "доставка": ["обслуживание", "еда"],
    "еда": ["кофе", "цена"],
}


def careful(true, acc):
    if rng.random() < acc:
        return true
    if rng.random() < 0.8:
        return rng.choice(NEAR[true])
    return rng.choice([t for t in TOPICS if t != true])


def hasty(true):
    if rng.random() < 0.33:
        return TOPICS[0]
    return careful(true, 0.8)


def main():
    r = pd.read_csv(DATA / "reviews_text.csv")
    sample = r.sample(450, random_state=1307).reset_index(drop=True)
    rows = []
    for rid, true in zip(sample["review_id"], sample["topic"]):
        rows.append((rid, "аня", careful(true, 0.90)))
        rows.append((rid, "борис", careful(true, 0.84)))
        rows.append((rid, "вика", hasty(true)))
    labels = pd.DataFrame(rows, columns=["review_id", "annotator", "label"])
    labels = labels.sample(frac=1, random_state=7).reset_index(drop=True)
    labels.to_csv(DATA / "review_labels.csv", index=False)

    gold = sample.sample(50, random_state=11)[["review_id", "topic"]].rename(columns={"topic": "label"})
    gold.sort_values("review_id").to_csv(DATA / "review_gold.csv", index=False)
    print(f"review_labels.csv: {len(labels)} строк; review_gold.csv: {len(gold)} строк")


if __name__ == "__main__":
    main()
