"""Запуск: python expert-probes.py ЭКСПОРТ.json. Исходные файлы курса остаются неизменными."""
import json
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/"site/assets"))
import harness

items = {(t["lesson"], t.get("id")):t for t in json.loads(Path(sys.argv[1]).read_text()) if t["kind"] == "task"}

def probe(lesson, task, label, transform, expected, prepare=None):
    item = items["ch03/"+lesson, task]
    previous = Path.cwd()
    with TemporaryDirectory() as folder:
        os.chdir(folder)
        try:
            for filename in item["files"]:
                shutil.copyfile(ROOT/"site/data"/filename, filename)
            if prepare is not None:
                prepare()
            code = transform(item["solution"])
            result = harness.run(code, item["check"], item["setup"], False)
        finally:
            os.chdir(previous)
    actual = bool(result["ok"] and result["check"]["passed"])
    print(label, actual, result.get("check", {}).get("msg", ""))
    assert actual == expected, (label, result)

def alter_book():
    wb = openpyxl.load_workbook("zerno_finance.xlsx")
    for name, delta in [("План", 4), ("Факт", 2)]:
        ws = wb[name]
        ws.insert_rows(1, delta)
        ws.cell(1, 1, "Перенос формы")
        anchor = next(cell.row for cell in ws["A"] if cell.value == "Код")
        rows = {cell.value:cell.row for cell in ws["A"][anchor:]}
        for month in range(4, 13):
            ws.cell(rows["PRM-2"], month).value = 0
            ws.cell(rows["TMN-1"], month).value = None
    wb.save("zerno_finance.xlsx")

alt = '''
import pandas as pd
months = "Янв Фев Мар Апр Май Июн Июл Авг Сен".split()
heads, totals = {}, {}
for sheet, column in [("Факт", "факт"), ("План", "план")]:
    table = pd.read_excel("zerno_finance.xlsx", sheet_name=sheet, header=None)
    h = next(i for i, cell in table[0].items() if cell == "Код")
    heads[sheet] = h
    table.columns = table.iloc[h]
    shops = table.iloc[h+1:].set_index("Код").drop(index="Итого")
    totals[column] = shops[months].apply(pd.to_numeric).fillna(0).sum(axis="columns")
pf = pd.DataFrame(totals)[["план", "факт"]].round(1).sort_index(ascending=False)
'''
probe("03b-excel", "auto-header", "dynamic / independent heights and reversed shops", lambda _:alt, True, alter_book)
probe("03b-excel", "auto-header", "zero vs NA / wrong for entered sum", lambda _:alt.replace('.fillna(0).sum(axis="columns")', '.sum(axis=1, min_count=1)'), False, alter_book)
probe("03b-excel", "auto-header", "fixed 3/4", lambda source:source.replace('sheet[sheet[0] == "Код"].index[0]', '{"План": 3, "Факт": 4}[name]'), False)
def badphone():
    df = pd.read_csv("clients_raw.csv")
    df.loc[df.index[0], "phone"] = "+7 912 345-67-89 доб. 12"
    df.to_csv("clients_raw.csv", index=False)
probe("05-strings", "phone10", "valid format before slicing", lambda source:source, True, badphone)
probe("05-strings", "phone10", "blind suffix after injecting extension", lambda source:source.replace('digits.where(digits.str.fullmatch(r"[78]?\\d{10}")).str[-10:]', 'digits.str[-10:]'), False, badphone)
