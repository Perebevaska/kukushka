"""Контрпримеры главы 2. Запуск из корня Python с зависимостями курса и nbformat."""
import json
import os
import sys
import tempfile
import shutil
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'site/assets')]
import build
import harness
import make_notebooks
import nbformat

spec = importlib.util.spec_from_file_location('notebook_check', ROOT / 'site/notebooks/check_notebook.py')
notebook_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notebook_check)


def main():
    built = {}
    for source in (ROOT / 'content/ch02').glob('*.md'):
        if source.stem in ('intro', 'test'):
            continue
        build.CH_DISPLAY['ch02'] = True
        built[('ch02', source.stem)] = build.parse_lesson(source)
    with tempfile.TemporaryDirectory() as tmp:
        export = Path(tmp) / 'tasks.json'
        build.export(built, export)
        tasks = {(t['lesson'].split('/')[-1], t['id']): t for t in json.loads(export.read_text()) if t.get('kind') == 'task'}
        previous = Path.cwd()
        os.chdir(tmp)
        try:
            def probe(lesson, task, suffix='', expected=False, code=None):
                item = tasks[lesson, task]
                for filename in item.get('files', []):
                    shutil.copy(ROOT / 'site/data' / filename, filename)
                result = harness.run(code if code is not None else item['solution'] + '\n' + suffix, item['check'], item.get('setup'), False)
                passed = bool(result.get('check', {}).get('passed'))
                assert passed == expected, (lesson, task, suffix, result)
                print(f'OK {lesson}/{task}: {"accepted" if passed else "rejected"} {suffix[:65]}')
            for task, suffix in [
                ('load', "full.loc[0, 'city'] = 'Подменённый город'"),
                ('monthly', "monthly['orders'] = full.groupby(full.datetime.dt.to_period('M')).qty.sum()"),
                ('monthly', "monthly.index = monthly.index + 1"),
                ('shops', "by_shop['per_seat'] = 0"),
                ('heatmap', "load.iloc[0, 0] = 999"),
            ]:
                probe('09-project', task, suffix)
            for task, variable, column in [('p-city-month', 'city_month', 'month'), ('p-promo', 'promo_items', 'month'), ('p-cohorts', 'ret', 'cohort')]:
                probe('11-sql-project', task, f"import pandas as pd\n{variable}['{column}'] = pd.to_datetime({variable}['{column}']) + pd.DateOffset(months=1)")
            probe('07-duckdb', 'from-file', expected=True, code='''import duckdb
avg_check_delivery = duckdb.sql("SELECT round(avg(amount), 2) FROM read_csv('orders_3m.csv') WHERE channel = 'доставка'").fetchone()[0]''')
            probe('04b-pivot', 'g-unstack', expected=True, code='''import pandas as pd
df = pd.read_csv('orders_3m.csv')
wide = pd.crosstab(df.shop_id, df.channel, values=df.amount, aggfunc='sum')
wide_shape = wide.shape''')
            probe('09-project', 'verdicts', expected=True)
        finally:
            os.chdir(previous)
        # Шаблон первой ячейки выполняется и без sklearn; три CSV читаются из data/.
        template = make_notebooks.make_template()
        imports = next(c['source'] for c in template['cells'] if c['cell_type'] == 'code')
        if isinstance(imports, list):
            imports = ''.join(imports)
        compile(imports, '<template>', 'exec')
        print('OK template import cell compiles')
    for text, expected in [('.', False), ('123', False), ('Выручка выросла на 7 %. Для решения об акции нужен эксперимент.', True)]:
        nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell('## Итоги'), nbformat.v4.new_code_cell('x = 1'), nbformat.v4.new_markdown_cell(text)])
        report = notebook_check.Report(); notebook_check.check_sections(nb, report)
        assert (not report.errors) == expected, report.errors
    nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell('## Итоги'), nbformat.v4.new_code_cell('display(Markdown(conclusion))', outputs=[nbformat.v4.new_output('display_data', data={'text/markdown': 'Выручка выросла на 7 %. Для решения об акции нужен эксперимент.'})])])
    report = notebook_check.Report(); notebook_check.check_sections(nb, report)
    assert not report.errors, report.errors
    print('OK static / rendered Markdown; dot and bare number rejected')


if __name__ == '__main__':
    main()
