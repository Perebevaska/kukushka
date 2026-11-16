"""Run the expert's independently specified grade expectations against the course harness."""
import argparse
import json
import shutil
import sys
import tempfile
from contextlib import chdir
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "site/assets"))
import harness


def clean(text):
    return dedent(text).strip()


def variants(task):
    key = (task["lesson"], task["id"])
    reference = task["solution"]

    if key == ("ch01/exam-1", "parse"):
        prefix = clean(r'''
            def parse_line(line):
                city, qty, unit = line.split(";")
                return [city, int(qty), int(unit)]

            text = "Пермь;412;205\nКазань;538;198\n\nТюмень;297;214\n"
            rows = list(map(parse_line, filter(None, text.splitlines())))
        ''')
        return [
            (True, "map применяет parse_line к каждой непустой строке", prefix + "\ntotal = sum(qty * unit for _, qty, unit in rows)\nprint(rows, total)"),
            (False, "Пропущена выручка последнего города", reference + "\ntotal -= cups * price\nprint(total)"),
        ]

    if key == ("ch02/11-sql-project", "p-unsold"):
        code = clean("""
            import duckdb as db
            unsold = [row[0] for row in db.sql('''
                SELECT m.name FROM menu m WHERE NOT EXISTS
                (SELECT 1 FROM items i WHERE i.item_id=m.item_id)
            ''').fetchall()]
            lemonade_first = db.sql('''
                SELECT CAST(MIN(o.ordered_at) AS DATE) FROM orders o
                JOIN items i USING(order_id) JOIN menu m USING(item_id)
                WHERE m.name='Лимонад'
            ''').fetchone()[0]
            print(unsold, lemonade_first)
        """)
        return [(True, "Антисоединение через NOT EXISTS и дата первой продажи", code),
                (False, "Взята последняя дата продажи лимонада", code.replace("MIN(o.", "MAX(o."))]

    if key == ("ch03/03b-excel", "auto-header"):
        old = 'row = sheet[sheet[0] == "Код"].index[0]'
        return [(True, "Поиск заголовка по содержимому через перечисление ячеек", reference.replace(old, 'row = next(i for i, v in enumerate(sheet.iloc[:, 0]) if v == "Код")') + "\nprint(heads)"),
                (False, "Высоты листов переписаны из единственной книги", reference.replace(old, 'row = {"План": 3, "Факт": 4}[name]') + "\nprint(heads)")]

    if key == ("ch04/07c-metrics", "funnel-platform"):
        alt = reference.replace('f.pivot_table(index=["platform", "period"], columns="step", values="session_id", aggfunc="nunique")[steps]',
                                'f.groupby(["platform", "period", "step"]).session_id.nunique().unstack()[steps]')
        return [(True, "Уникальные сессии через groupby и unstack", alt),
                (False, "Таблица приписывает конверсии Android платформе iOS и наоборот", alt + '\npay_conv = pay_conv.rename(index={"android": "ios", "ios": "android"}, level=0)\nprint(pay_conv)')]

    if key == ("ch05/08-pitfalls", "practical"):
        code = clean("""
            from scipy.stats import chi2_contingency
            a, b = 400_000 / 2_000_000, 402_400 / 2_000_000
            p_value = chi2_contingency([[400000, 1600000], [402400, 1597600]], correction=False).pvalue
            diff_pp = round(100 * (b - a), 2)
            rel_pct = round(100 * (b / a - 1), 1)
            worth_it = bool(p_value < 0.05 and rel_pct >= 2)
            print(p_value, diff_pp, rel_pct, worth_it)
        """)
        return [(True, "Двусторонняя проверка долей через эквивалентный критерий Пирсона без коррекции", code),
                (False, "Решение только по значимости, без порога относительного роста", code.replace(" and rel_pct >= 2", ""))]

    if key == ("ch06/04-categorical", "shop-rate"):
        alt = reference.replace('y_train.groupby(X_train["shop_id"]).mean()', 'X_train.assign(late=y_train).groupby("shop_id")["late"].mean()')
        diag = '\nprint("диапазон, п.п.", diff, "кофеен", len(shop_rate))'
        return [(True, "Агрегация метки после выравнивания по ID строк train", alt + diag),
                (False, "Признак рассчитан и на будущих тестовых метках", alt.replace('X_train.assign(late=y_train).groupby("shop_id")["late"].mean()', 'y.groupby(ok["shop_id"]).mean()') + diag),
                (False, "Сортировка только shop_id переносит кофейни к чужим долям в X_test",
                 alt + '\nX_test["shop_id"] = X_test["shop_id"].sort_values().to_numpy()\nprint("неверных долей", (X_test["shop_rate"] != X_test["shop_id"].map(shop_rate)).sum(), "из", len(X_test))'),
                ]

    if key == ("ch07/03-threshold", "roc-plot"):
        short = 'ax.plot([0, 1], [0, 1], color="grey", linestyle="--")'
        dense = reference.replace(short, 'ax.plot([0, .25, .75, 1], [0, .25, .75, 1], "--")')
        diag = '\nprint("точек ROC", len(fpr), "AUC", auc, "диагональ", list(ax.lines[1].get_ydata()))'
        return [(True, "Все промежуточные точки ROC сохранены, диагональ построена по четырём узлам", dense.replace('roc_curve(y_test, p)', 'roc_curve(y_test, p, drop_intermediate=False)') + diag),
                (False, "Одна внутренняя точка случайного классификатора лежит выше диагонали", dense.replace('[0, .25, .75, 1], "--"', '[0, .65, .75, 1], "--"') + diag),
                (True, "Контроль с сокращённой ROC и четырьмя узлами диагонали", dense + diag)]

    if key == ("ch08/06-project", "decision"):
        code = clean("""
            passed = [city for city, p in risk.p_loss.items() if p <= .025]
            choice = max(passed, key=risk["mean"].get) if passed else None
            cost_of_safety = risk["mean"].max() - risk.at[choice, "mean"] if passed else None
            print(passed, choice, cost_of_safety)
        """)
        return [(True, "Список по индексу, max среди прошедших, ветка без запуска", code),
                (False, "Исключён город с риском ровно 2.5 %", code.replace("p <= .025", "p < .025"))]

    if key == ("ch09/03-normal-equation", "many-solutions"):
        # Fit on the independent four-column basis and restore the omitted coefficient.
        code = reference.replace('np.linalg.lstsq(full, y, rcond=None)[0]',
                                 'np.r_[np.linalg.lstsq(full[:, :-1], y, rcond=None)[0], 0.]')
        diag = '\nprint(w_a, w_b, max_diff, weights_differ)'
        return [(True, "Коэффициент последнего флага фиксирован нулём, МНК по независимым столбцам", code + diag),
                (False, "Та же минимальная ошибка, но сдвиг обоих решений на 9 вместо требуемых 10", code.replace('+= 10', '+= 9').replace('-= 10', '-= 9') + diag)]

    if key in (("ch10/05-project", "compare"), ("ch10/06-libraries", "speed-table")):
        if key[1] == "compare":
            alt = reference.replace("best = min(validation_scores, key=validation_scores.get)", "best = pd.Series(validation_scores).idxmin()")
            wrong = alt.replace("fit_s = time.perf_counter() - t0", "fit_s = 90.0")
            return [(True, "Выбор по минимуму Series валидационных ошибок и фактический замер", alt),
                    (False, "Для всех пяти обучений внесены вымышленные 90 секунд, nightly_ok=False", wrong)]
        alt = reference.replace('fastest_fit = table["fit_s"].idxmin()', 'fastest_fit = min(table.index, key=table["fit_s"].get)')
        wrong = alt.replace('fit_s = time.perf_counter() - t0',
                            'fit_s = {"GradientBoosting": .001, "HistGradientBoosting": .4, "RandomForest": .2}[name]')
        return [(True, "Измерены времена perf_counter, победитель найден функцией min по фактической колонке", alt),
                (False, "Времена полностью назначены по имени модели, fastest_fit взят из выдуманной таблицы", wrong)]

    if key == ("ch11/04b-softmax", "batches"):
        code = reference.replace('for start in range(0, len(y), size):\n        idx = order[start:start + size]',
                                 'for idx in np.split(order, np.arange(size, len(y), size)):')
        diag = '\nfor seed in (0, 17):\n    print("seed", seed, np.concatenate([b for _, b in batches(X,y,4,np.random.default_rng(seed))]))'
        return [(True, "Нарезка перестановки np.split с остатком", code + diag),
                (False, "Одна фиксированная перестановка повторяется при каждом seed и в каждой эпохе", code.replace("rng.permutation(len(y))", "np.random.default_rng(0).permutation(len(y))") + diag)]

    if key == ("ch12/04-forecast", "wape"):
        alt = reference.replace("np.abs(fact - pred).sum() / fact.sum()", "sum(abs(a - b) for a, b in zip(fact, pred)) / sum(fact)")
        diag = '\nprint(w, zeros)'
        return [(True, "Сумма абсолютных ошибок по парам часов, включая нулевые", alt + diag),
                (False, "Нулевые факты исключены и из числителя WAPE", alt.replace("zip(fact, pred))", "zip(fact, pred) if a != 0)") + diag)]

    if key == ("ch13/04c-llm", "parse-llm"):
        code = reference.replace('pd.DataFrame([parse(a) for a in raw])', 'pd.DataFrame.from_records(map(parse, raw))')
        return [(True, "Сохранены порядок и все значения, строки пронумерованы с единицы", code + '\nparsed.index = range(1, len(parsed) + 1)\nprint(parsed)'),
                (False, "Допустимые темы ограничены пятью вместо шести, новый ответ про еду отвергнут",
                 code.replace('not in TOPICS', 'not in [t for t in TOPICS if t != "еда"]') + '\nprint(parse(\'{"sentiment":"positive","topic":"еда"}\'))'),
                (True, "Контроль с таким же разбором через map и началом индекса с нуля", code)]

    if key == ("ch14/04c-detection", "iou"):
        code = reference.replace('inter = max(0, w) * max(0, h)', 'inter = w * h if min(w, h) > 0 else 0')
        return [(True, "Обнуление пересечения при неположительном перекрытии любой оси", code),
                (False, "Сначала перемножены два отрицательных перекрытия, затем результат обрезан нулём", code.replace("w * h if min(w, h) > 0 else 0", "max(0, w * h)"))]

    if key == ("ch15/05-project", "guard"):
        code = reference.replace('if row["visits_90d"] < 0:', 'if not row["visits_90d"] >= 0:')
        diag = '\nprint("отрицательные визиты", range_problems(dict(avg_check=800, delivery_share=.5, visits_90d=-1)))'
        return [(True, "Три проверки, отдельно доли отказа и время первого инцидента", code + diag),
                (False, "Потеряна проверка отрицательного числа визитов", code.replace('    if not row["visits_90d"] >= 0:\n        problems.append("visits_90d: ожидается ≥ 0")\n', "") + diag)]

    return []


def run(export, chapter=None, emit=False):
    tasks = json.loads(Path(export).read_text())
    for item in sorted(tasks, key=lambda row: row["lesson"][:4]):
        if item["kind"] != "task" or (chapter and item["lesson"].split("/")[0] not in chapter):
            continue
        for expected, description, code in variants(item):
            if emit:
                print(json.dumps(dict(lesson=item["lesson"], task=item["id"], expected=expected,
                                      description=description, code=code), ensure_ascii=False))
                continue
            with tempfile.TemporaryDirectory() as work, chdir(work):
                for filename in item["files"]:
                    shutil.copy2(ROOT / "site/data" / filename, filename)
                result = harness.run(code, item["check"], item.get("setup"))
            print(json.dumps(dict(lesson=item["lesson"], task=item["id"], expected=expected,
                                  description=description, ok=result["ok"], passed=result["check"]["passed"],
                                  message=result["check"]["msg"], stdout=result["out"], error=result["error"]),
                             ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("export")
    parser.add_argument("chapter", nargs="*")
    parser.add_argument("--emit", action="store_true", help="Emit complete programs and predeclared verdicts as JSONL")
    args = parser.parse_args()
    run(args.export, args.chapter, emit=args.emit)
