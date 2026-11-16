"""Повторить независимые пробы: python expert_probes.py <свежий экспорт build.py>."""
import csv
import inspect
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "site/assets"))
from harness import run


def build_report(orders):
    from collections import Counter
    if not orders:
        return "# Отчёт\nНет принятых заказов"
    cities, days = Counter(), Counter()
    for row in orders:
        cities[row["city"]] += row["amount"]
        days[row["date"].weekday()] += row["amount"]
    drinks = Counter(row["drink"] for row in orders)
    top = sorted(drinks, key=lambda drink: (-drinks[drink], drink))[:3]
    names = "понедельник вторник среда четверг пятница суббота воскресенье".split()
    city, day = max(cities, key=cities.get), max(days, key=days.get)
    revenue = sum(cities.values())
    return "\n".join([
        f"# Отчёт за {orders[0]['date']:%Y-%m}",
        f"Принято заказов: {len(orders)}", f"Учтённая выручка: {revenue} ₽",
        f"Средний чек: {round(revenue / len(orders))} ₽",
        f"Лучший город: {city} — {cities[city]} ₽",
        "Напитки по числу заказов: " + ", ".join(f"{d} ({drinks[d]})" for d in top),
        f"День с наибольшей выручкой: {names[day]} — {days[day]} ₽",
    ])


def write_report():
    import csv
    from datetime import date
    from pathlib import Path
    with open("orders.csv", encoding="utf-8", newline="") as source:
        records = list(csv.DictReader(source))
    accepted = {}
    bad, duplicates = 0, 0
    for row in records:
        try:
            row["amount"] = int(row["amount"])
        except ValueError:
            bad += 1
            continue
        if row["order_id"] in accepted:
            duplicates += 1
            continue
        row["date"] = date.fromisoformat(row["date"])
        accepted[row["order_id"]] = row
    report = build_report(list(accepted.values()))
    journal = ["## Качество данных", f"- Строк в выгрузке: {len(records)}",
               f"- Битых строк: {bad}", f"- Дублей: {duplicates}"]
    Path("report.md").write_text(report + "\n\n" + "\n".join(journal), encoding="utf-8")


def main(export_path):
    items = json.loads(export_path.read_text())
    tasks = {(t["lesson"].split("/")[-1], t["id"]): t for t in items
             if t["lesson"].startswith("ch01/") and t["kind"] == "task"}
    expected = {
        "верный парсер": True, "пропуск третьего города": False,
        "группировка по параметру": True, "группировка только по городу": False,
        "другая функция отчёта": True, "другая программа файла": True,
        "счёт только чашек": False, "умножение чашек на цену": True,
        "название вместо частоты в цикле": False, "длина названия вместо частоты": False,
    }
    def grade(label, key, code):
        t = tasks[key]
        result = run(code, t["check"], t["setup"])["check"]
        print(label, "ожидание", expected[label], "факт", result["passed"], result["msg"])
        return result["passed"]

    def install(rows):
        with open("orders.csv", "w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["order_id", "date", "city", "drink", "amount"])
            writer.writerows(rows)

    csv_bytes = (ROOT / "site/data/orders.csv").read_bytes()
    previous = Path.cwd()
    try:
        with TemporaryDirectory() as folder:
            os.chdir(folder)
            Path("orders.csv").write_bytes(csv_bytes)
            parse = tasks["exam-1", "parse"]["starter"].replace("    ...", (
                "    city, cups, price = line.split(';')\n    return [city, int(cups), int(price)]"))
            parse += "\nrows = map(parse_line, filter(str.strip, text.splitlines()))\ntotal = sum(cups * price for city, cups, price in rows)"
            assert grade("верный парсер", ("exam-1", "parse"), parse)
            assert not grade("пропуск третьего города", ("exam-1", "parse"), parse + "\nif 'Тюмень' in text: total -= 297 * 214")
            revenue_by = ("def revenue_by(orders, field):\n    from collections import Counter\n"
                          "    totals = Counter()\n    for row in orders:\n        totals[row[field]] += row['amount']\n    return dict(totals)")
            assert grade("группировка по параметру", ("exam-1", "revenue-by"), revenue_by)
            assert not grade("группировка только по городу", ("exam-1", "revenue-by"), revenue_by.replace("row[field]", "row['city']"))
            for label, key in [("умножение чашек на цену", "row[1] * row[2]"), ("счёт только чашек", "row[1]")]:
                t = tasks["07-tables", "best-city"]
                code = t["starter"] + "\nbest_city = max(sales, key=lambda row: " + key + ")[0]"
                grade(label, ("07-tables", "best-city"), code)
            t = tasks["08-dicts", "top"]
            code = t["starter"] + ('\ntop_drink = ""\nfor drink, count in counts.items():'
                                   '\n    if drink > top_drink:\n        top_drink, top_count = drink, count')
            grade("название вместо частоты в цикле", ("08-dicts", "top"), code)
            t = tasks["11-comprehensions", "top-key"]
            grade("длина названия вместо частоты", ("11-comprehensions", "top-key"),
                  t["starter"] + "\ntop = max(counts, key=len)")
            fn = inspect.getsource(build_report)
            program = fn + "\n" + inspect.getsource(write_report) + "\nwrite_report()"
            assert grade("другая функция отчёта", ("14-project", "report"), fn)
            assert grade("другая программа файла", ("14-project", "file"), program)
            print("Сентябрь\n" + Path("report.md").read_text())
            headers = ["A", "2028-01-03", "Клин", "Чай"]
            install([headers + ["—"], headers + [125], headers + [1000],
                     ["B", "2028-01-04", "Бор", "Какао", 310],
                     ["C", "2028-01-03", "Клин", "Чай", 170]])
            assert grade("другая программа файла", ("14-project", "file"), program)
            print("Новый январь\n" + Path("report.md").read_text())
            names = ["Американо", "Бабл-ти", "Дарджилинг", "Ёжевичный чай"]
            install([[str(i), "2028-02-01", "Бор", name, 100] for i, name in enumerate(names)])
            card = tasks["14-project", "file"]
            for label, text in [("ключ Python", program),
                                ("порядок Д, Е/Ё, Ж", program.replace("(-drinks[drink], drink)",
                                                                      '(-drinks[drink], drink.casefold().replace("ё", "е"))'))]:
                actual = run(text, card["check"], card["setup"])["check"]
                top = next(line for line in Path("report.md").read_text().splitlines() if line.startswith("Напитки"))
                print(label, actual, top)
            outputs = []
            for month in ("11", "12"):
                install([["N1", f"2027-{month}-02", "Клин", "Чай", "—"],
                         ["N2", f"2027-{month}-03", "Клин", "Чай", ""]])
                result = run(tasks["14-project", "file"]["solution"],
                             tasks["14-project", "file"]["check"], tasks["14-project", "file"]["setup"])
                assert result["check"]["passed"], result
                outputs.append(Path("report.md").read_bytes())
                print("Все суммы битые", month, result["check"], outputs[-1].decode())
            assert outputs[0] == outputs[1]
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
