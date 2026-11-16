"""Check the two-sheet report written by the published Excel notebook."""
from contextlib import chdir, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / 'site/data/zerno_finance.xlsx'
NOTEBOOK = ROOT / 'site/notebooks/extra/ch03-excel.ipynb'
MONTHS = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен']


def row_of(sheet, label):
    return next(cell.row for cell in sheet['A'] if cell.value == label)


def run_case(mode):
    with TemporaryDirectory() as tmp, chdir(tmp):
        data = Path('data')
        data.mkdir()
        book = openpyxl.load_workbook(BOOK)
        if mode != 'исходная':
            for name, shift in [('План', 1), ('Факт', 4)]:
                sheet = book[name]
                sheet.insert_rows(1, shift)
                if mode == 'явные нули':
                    row = row_of(sheet, 'EKB-1')
                    for col in range(4, 13):
                        sheet.cell(row, col).value = 0
            if mode == 'пропущен месяц':
                sheet = book['Факт']
                row = row_of(sheet, 'KZN-2')
                total = sheet.cell(row_of(sheet, 'Итого'), 4)
                total.value -= sheet.cell(row, 4).value
                sheet.cell(row, 4).value = None
        book.save(data / BOOK.name)
        ns = {}
        with redirect_stdout(io.StringIO()):
            for cell in json.loads(NOTEBOOK.read_text())['cells']:
                if cell['cell_type'] == 'code':
                    exec(''.join(cell['source']), ns)
        sheets = pd.read_excel('plan_fact_report.xlsx', sheet_name=None)
        assert list(sheets) == ['Выполнение', 'Факт без итога']
        report = sheets['Выполнение'].set_index('Код')
        raw = sheets['Факт без итога'].set_index('Код')
        assert len(report) == len(raw) == 7 and set(report.index) == set(raw.index)
        zero = report.loc['EKB-1']
        n = 9 if mode == 'явные нули' else 0
        assert zero['сумма внесённого плана, тыс. ₽'] == zero['сумма внесённого факта, тыс. ₽'] == 0
        assert zero['месяцев плана'] == zero['месяцев факта'] == raw.loc['EKB-1', MONTHS].count() == n
        assert pd.isna(zero['выполнение, %'])
        kzn = report.loc['KZN-2']
        if mode == 'пропущен месяц':
            assert kzn['месяцев факта'] == 8 and pd.isna(kzn['выполнение, %'])
        else:
            assert kzn['месяцев факта'] == 9 and kzn['выполнение, %'] == 85.6
        return {'case': mode, 'shops': len(report), 'sheets': list(sheets),
                'ekb_recorded_months': int(zero['месяцев факта']), 'kzn_recorded_months': int(kzn['месяцев факта']),
                'kzn_percentage': None if pd.isna(kzn['выполнение, %']) else float(kzn['выполнение, %'])}


if __name__ == '__main__':
    print(json.dumps([run_case(case) for case in ('исходная', 'явные нули', 'пропущен месяц')], indent=2, ensure_ascii=False))
