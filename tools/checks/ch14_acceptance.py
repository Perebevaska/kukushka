import json
import re
import pandas as pd
from acceptance_runner import Chapter, ROOT

with Chapter('ch14') as c:
    c.probe('05-project','hours','df=df.sample(frac=1,random_state=2)',expected=True)
    c.probe('05-project','hours','df["pred"]=df["pred"].iloc[::-1].to_numpy()')
    c.probe('05-project','fix','pred_norm=pred_norm[::-1]')
    c.probe('05-project','alerts',expected=True)
    c.probe('05-project','restock',expected=True)
    c.probe('05-project','restock','schedule_scenarios.loc["перенос","whole_day"]=0')
    c.probe('05-project', 'alerts', 'chosen_k = 1 if chosen_k != 1 else 3')
    c.probe('05-project', 'alerts', 'policy_table.loc[1, "delay_total"] += 15')
    c.probe('05-project', 'alerts', 'next_metrics = episode_metrics(df, alert_table(df, chosen_k))')

    project = '05-project'
    light = c.tasks[project, 'light']['solution']
    calculation = light.split('ax = bright.plot', 1)[0]
    old_attempts = ROOT / 'docs/audit-2026-11-13/ch14/browser.jsonl'
    old_light = next(row['code'] for row in map(json.loads, old_attempts.read_text().splitlines())
                     if row['lesson'] == project and row.get('id') == 'light' and row['passed'])
    c.probe(project, 'light', code=old_light, expected=True)
    walkthrough = ROOT / 'docs/course-improvements/ch14/cost-and-light-retest.md'
    attempts = [code for code in re.findall(r'```python\n(.*?)\n```', walkthrough.read_text(), re.S)
                if 'frame_brightness = X.reshape' in code]
    raw_empty, raw_graph = attempts[:2]
    raw_feedback = c.probe(project, 'light', code=raw_empty)['check']['msg']
    assert 'График пуст' in raw_feedback and '0–255' in raw_feedback
    c.probe(project, 'light', code=raw_graph, expected=True)
    c.probe(project, 'light', code=raw_graph.replace('X = data["X"]', 'X = data["X"] / 255'), expected=True)
    for code, unit in [
        (raw_graph.replace('ax.plot(x, bright.to_numpy()', 'ax.plot(x, bright.to_numpy() / 255'), '0–255'),
        (calculation + '\n(bright * 255).plot()', '0–1'),
    ]:
        feedback = c.probe(project, 'light', code=code)['check']['msg']
        assert 'Шкалы не совпали' in feedback and unit in feedback
    invalid = raw_graph + '\nbright *= 0.5'
    assert 'значения bright' in c.probe(project, 'light', code=invalid)['check']['msg']
    c.probe(project, 'light', code=raw_graph + '\nbright.iloc[4] = float("nan")')
    c.probe(project, 'light', code=raw_graph + '\nbright = bright.astype(str)')
    for drawing in [
        'plt.plot(bright.index, bright.values)',
        'plt.scatter(bright.index, bright.values)',
        'plt.plot(pd.to_datetime("2000-01-01 " + bright.index), bright.values)',
        'bright.set_axis(pd.to_datetime("2000-01-01 " + bright.index)).plot()',
        'bright.sample(frac=1, random_state=2).pipe(lambda s: plt.scatter(pd.to_datetime("2000-01-01 " + s.index), s.values))',
        'plt.plot(range(61), bright.values); plt.xticks(range(0,61,12), bright.index[::12])',
        'plt.plot(bright.index, bright.values); bright = bright.sample(frac=1, random_state=2)',
    ]:
        c.probe(project, 'light', code=calculation + '\n' + drawing, expected=True)

    empty = c.probe(project, 'light', code=calculation + '\nplt.subplots()')
    wrong = c.probe(project, 'light', code=calculation + '\nplt.plot(bright.index, bright.values[::-1])')
    assert 'График пуст' in empty['check']['msg'] and '61 пара' in wrong['check']['msg']
    for suffix in [
        'bright = bright.set_axis(bright.index[::-1])',
        'bright = bright.reset_index(drop=True)',
        'ax.lines[0].set_visible(False)',
        'ax.set_xlim(0, 20)',
        'ax.lines[0].set_ydata(bright.where(bright.index != "18:00", 0).values)',
        'ax.set_xticks([0, 60], ["22:00", "07:00"])',
    ]:
        c.probe(project, 'light', suffix)
    c.probe(project, 'light', code=calculation + '\nplt.plot(range(61), bright)')
    c.probe(project, 'light', code=calculation + '\nplt.plot(bright.index[::2], bright.values[::2])')

    # Use the same episode and alert definitions as the assignment, on its two short logs.
    # ML predictions are already in the log. Only the scoring functions are needed here.
    item = c.tasks[project, 'alerts']
    scope = {}
    exec(item['setup'], scope)
    exec(item['solution'], scope)

    def short_log(start, truth, model):
        times = pd.date_range('2026-01-01 ' + start, periods=len(truth), freq='15min').strftime('%H:%M')
        # The question labels emptiness as 1. Project class 0 means empty.
        return pd.DataFrame({'time': times, 'slot': 0, 'true': [1-x for x in truth], 'pred': [1-x for x in model]})

    def losses(day, fee):
        result = {}
        for k in (1, 2, 3):
            m = scope['episode_metrics'](day, scope['alert_table'](day, k))
            result[k] = fee * m['false'] + 300 * m['missed'] + m['delay_total']
        return result

    first = short_log('09:00', [0,0,0,1,1,1,0,0,0,0], [1,0,0,1,1,1,0,1,0,0])
    second = short_log('12:30', [0,1,1,0,0,0], [1,1,0,0,1,0])
    old, new = losses(first, 45), losses(first, 6)
    assert old == {1: 90, 2: 15, 3: 30} and new == {1: 12, 2: 15, 3: 30}
    fixed_k = min(new, key=new.get)
    held_out = losses(second, 6)
    assert fixed_k == 1 and held_out == {1: 312, 2: 0, 3: 300}
    print('OK short alert logs: fee 45 → 6 changes k from 2 to 1; fixed k=1 costs 312 on day 2')
