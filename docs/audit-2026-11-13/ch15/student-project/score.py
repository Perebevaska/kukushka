"""Составить список звонков на дату квартального среза."""
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from src.features import read_tables, build_features

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "models/office_churn/1.0"


def call_profit(monthly_revenue, risk, economy):
    benefit = risk * economy["save"] * economy["margin"] * economy["months"] * monthly_revenue
    cost = economy["call_cost"] + economy["discount"] * economy["discount_months"] * monthly_revenue
    return benefit - cost


def rank_clients(features, probabilities, economy):
    report = features[["city"]].reset_index()
    report["p_churn"] = probabilities
    report["exp_profit"] = call_profit(features.revenue_90.to_numpy() / 3, probabilities, economy)
    return (report.loc[report.exp_profit > 0]
            .sort_values(["exp_profit", "client_id"], ascending=[False, True])
            .head(economy["limit"]).reset_index(drop=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--db", type=Path, default=ROOT / "data/office.db")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    cutoff = pd.Timestamp(args.cutoff)
    if not cutoff.is_quarter_end:
        parser.error("Укажите последний день квартала")
    tables = read_tables(args.db)
    if cutoff > tables["orders"].order_date.max():
        parser.error("Выгрузка не содержит полный запрошенный срез")
    with (ARTIFACT / "passport.json").open() as stream:
        card = json.load(stream)
    model = joblib.load(ARTIFACT / "model.joblib")
    x = build_features(tables, cutoff)[card["features"]]
    probabilities = model.predict_proba(x)[:, 1]
    report = rank_clients(x, probabilities, card["economy"])
    path = args.out or ROOT / "reports" / f"call_list_{cutoff.date()}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    report.round({"p_churn": 3, "exp_profit": 0}).to_csv(path, index=False)
    print(f"{cutoff.date()} | действующих {len(x)} | звонков {len(report)} | ожидаемая прибыль {report.exp_profit.sum():,.0f} ₽")


if __name__ == "__main__":
    main()
