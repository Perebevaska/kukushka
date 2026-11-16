"""Показать вердикты штатных проверок спорным решениям на копиях данных главы 1."""
import json
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "site" / "assets"))
import harness


def check(task_id, code, label):
    """Запустить обычный проверяющий код задания и показать ожидаемый учеником эффект."""
    task = tasks[f"ch01/{task_id}"]
    with TemporaryDirectory() as tmp:
        for name in task["files"]:
            shutil.copyfile(ROOT / "site" / "data" / name, Path(tmp) / name)
        original = Path.cwd()
        try:
            os.chdir(tmp)
            result = harness.run(code, task["check"], task["setup"])
        finally:
            os.chdir(original)
    verdict = result.get("check") or {}
    message = verdict.get("msg") or (result.get("error") or {}).get("text", "")
    print(f"{task_id} · {label} — {'принято' if verdict.get('passed') else 'отклонено'}")
    if message:
        print(" ", message)


if __name__ == "__main__":
    tasks = json.loads((ROOT / "site/notebooks/tasks/ch01.json").read_text())["tasks"]
    load = tasks["ch01/14-project/load"]["solution"]
    check("14-project/load", load + "\nfor row in orders:\n    row['amount'] = 0",
          "у всех заказов обнулили сумму")

    csv_task = tasks["ch01/13-files/write"]["solution"]
    check("13-files/write",
          "with open('by_city.csv', 'w', encoding='utf-8') as out:\n"
          "    out.write('city,revenue Пермь,1450 Казань,600 Тюмень,715')",
          "одна физическая строка вместо четырёх")
    check("13-files/write", csv_task.replace("csv.writer(f)", "csv.writer(f, quoting=csv.QUOTE_ALL)"),
          "правильный CSV с кавычками")

    report = tasks["ch01/14-project/file"]["solution"]
    check("14-project/file", report, "эталон без напитков и дня недели")
    check("14-project/file", report + "\nwith open('report.md', 'a', encoding='utf-8') as out:\n"
          "    print('Напитки по заказам: Американо — 9, Раф — 8, Флэт уайт — 8', file=out)\n"
          "    print('День с наибольшей выручкой: среда (5 070 ₽)', file=out)",
          "тот же файл с двумя ответами на вопросы руководителя")
