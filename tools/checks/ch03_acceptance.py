from acceptance_runner import Chapter
import pandas as pd

with Chapter('ch03') as chapter:
    for task, suffix in [
        ('age', "clients['age'] = clients['age'].shift(1, fill_value=clients['age'].iloc[-1])"),
        ('guests', "guests['orders'] = 1"),
        ('sources', "by_source.iloc[0, by_source.columns.get_loc('avg_revenue')] = float('nan')"),
        ('age-money', "by_age.iloc[0, by_age.columns.get_loc('avg_orders')] = float('nan')"),
    ]:
        chapter.probe('09-project', task, suffix)
    task = chapter.tasks['09-project', 'report']
    fixed = task['solution'].replace('def report(raw, orders):', 'def report(raw, orders):\n    raw = pd.read_csv("clients_raw.csv")')
    chapter.probe('09-project', 'report', code=fixed)
    for lesson, task in [('08-pipeline','full'), ('09-project','clean')]:
        chapter.probe(lesson, task, expected=True)
        source=chapter.tasks[lesson, task]['solution']
        bad=source.replace('return digits.where(ok).str[-10:]', 'return digits.str[-10:]')
        chapter.probe(lesson, task, code=bad)
    chapter.probe('08-pipeline','fn-gender', code='def clean_gender(s):\n    return s.str.strip().str.lower().str[0].map({"м":"М","ж":"Ж"})')
    def extra_header():
        import openpyxl
        workbook=openpyxl.load_workbook('zerno_finance.xlsx')
        for sheet in ('План','Факт'):
            workbook[sheet].insert_rows(1)
            workbook[sheet].cell(1,1,'Предварительные данные')
        workbook.save('zerno_finance.xlsx')
    chapter.probe('03b-excel','auto-header',prepare=extra_header,expected=True)
