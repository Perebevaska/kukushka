"""Повторить приёмку главы 1 по собранным карточкам, сохранив учебные CSV и прогресс."""
from contextlib import chdir
import csv
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "site/assets"))
from harness import run


def submit(tasks, key, code, passed, message=""):
    task = tasks["ch01/" + key]
    with TemporaryDirectory() as folder, chdir(folder):
        for name in task["files"]:
            shutil.copyfile(ROOT / "site/data" / name, name)
        result = run(code, task["check"], task["setup"])
        verdict = result["check"]
        assert verdict["passed"] == passed and message in verdict["msg"], (key, verdict, result["error"])
        if key == "14-project/file" and passed:
            return Path("report.md").read_bytes()


def main():
    tasks = json.loads((ROOT / "site/notebooks/tasks/ch01.json").read_text())["tasks"]
    journal = (ROOT / "docs/audit-2026-11-13/ch01/browser.jsonl").read_text().splitlines()
    old = {f'{r["lesson"]}/{r["id"]}': r["code"] for line in journal
           if (r := json.loads(line)).get("passed") and "code" in r}
    assert {f"ch01/{k}" for k in old} == set(tasks)
    checkpoint = "exam-1/revenue-by"
    walkthrough = (HERE / "cognitive-walkthrough.jsonl").read_text().splitlines()
    attempts = [r["code"] for line in walkthrough if (r := json.loads(line)).get("id") == "revenue-by"
                and r["event"] == "answer-before"]
    assert len(attempts) == 2
    for program in attempts:
        submit(tasks, checkpoint, program, True)
    memorized = """def revenue_by(orders, field):
    if not orders:
        return {}
    if field == "city":
        return {"Пермь": 1060, "Казань": 320}
    return {"Латте": 450, "Раф": 930}
"""
    submit(tasks, checkpoint, memorized, False, "Сгруппируйте")
    changed_contract = {"14-project/report", "14-project/file"}
    for key, code in old.items():
        submit(tasks, key, code, key not in changed_contract)
    print(f"Архивные решения: {len(old) - len(changed_contract)} приняты, {len(changed_contract)} требуют обновлённого отчёта.")

    source = (HERE / "student-solution.py").read_text()
    project = "14-project/file"
    assert submit(tasks, project, source, True) == (HERE / "student-report.md").read_bytes()
    second_pass = (HERE / "student-retest-solution.py").read_text()
    assert submit(tasks, project, second_pass, True) == (HERE / "student-report.md").read_bytes()
    submit(tasks, project, source.replace('open("report.md", "w"', 'open("report.md", "a"'), False)
    submit(tasks, project, source.replace('orders[0]["date"].isoformat()[:7]', '"2026-09"'), False, "период")
    submit(tasks, project, source.replace("День с наибольшей выручкой:", "Комментарий:"), False, "День")
    for field, calc in [
        ("city", 'sum(row["city"] == key for row in orders)'),
        ("day", 'sum(row["date"].weekday() == key for row in orders)'),
    ]:
        group = "cities" if field == "city" else "days"
        wrong = source.replace(f"key={group}.get", f"key=lambda key: {calc}")
        submit(tasks, project, wrong, False)

    # Исполнить саму скачанную работу ученика без harness и без скрытой подготовки.
    october = [
        ("1", "2027-10-04", "Томск", "Чай", "80"),
        ("2", "2027-10-04", "Томск", "Чай", "120"),
        ("3", "2027-10-05", "Омск", "Какао", "700"),
        ("3", "2027-10-05", "Омск", "Какао", "850"),
        ("4", "2027-10-06", "Омск", "Матча", "—"),
    ]
    with TemporaryDirectory() as folder, chdir(folder):
        Path("report.md").write_bytes((HERE / "student-report.md").read_bytes())
        for rows in (october, []):
            with open("orders.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(("order_id", "date", "city", "drink", "amount"))
                writer.writerows(rows)
            exec(compile(source, "student-solution.py", "exec"), {"__name__": "__main__"})
            report = Path("report.md").read_text()
            if rows:
                for term in ("2027-10", "Принято заказов: 3\n", "Учтённая выручка: 900 ₽", "Средний чек: 300 ₽", "Омск (700 ₽)", "вторник (700 ₽)",
                             "Чай (2), Какао (1)", "Строк в выгрузке: 5", "Битых строк: 1", "Дублей: 1"):
                    assert term in report, term
            else:
                assert "Нет принятых заказов" in report and "2027-10" not in report
                for term in ("Строк в выгрузке: 0", "Битых строк: 0", "Дублей: 0"):
                    assert term in report
            assert "2026-09" not in report
    print("Файл ученика воспроизведён; проверки ошибок, смены месяца и пустой выгрузки прошли.")


if __name__ == "__main__":
    main()
