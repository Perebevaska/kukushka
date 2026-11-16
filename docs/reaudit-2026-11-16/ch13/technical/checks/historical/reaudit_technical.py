"""Re-run the exact 35 expert programs, then contract migrations and targeted pairs.

Run with the course Python environment from the repository root. --emit writes
current tasks/programs for the existing expert_pyodide.mjs runner without building
or mutating site. Historical evidence and this frozen fixture stay unchanged.
"""
import argparse
import json
import shutil
from pathlib import Path

from acceptance_runner import Chapter, ROOT
import harness

FIXTURE = Path(__file__).with_name('fixtures') / 'reaudit_20261115.jsonl'
MIGRATIONS = {'shop-rate', 'compare', 'speed-table'}


def current_tasks():
    result = {}
    for chapter in [f'ch{n:02}' for n in range(1, 16)]:
        with Chapter(chapter) as source:
            result.update({f'{chapter}/{lesson}/{task}': item for (lesson, task), item in source.tasks.items()})
    return result


def migrated(row):
    code, task = row['code'], row['task']
    if task == 'shop-rate':
        return code.replace('.map(shop_rate)', '.map(shop_rate).fillna(y_train.mean())')
    if task in ('compare', 'speed-table'):
        train, target, test = ('X[tr]', 'y[tr]', 'X[~tr]') if task == 'compare' else ('X_tr', 'y_tr', 'X_te')
        code = code.replace('    t0 = time.perf_counter()\n', '')
        code = code.replace(f'    model.fit({train}, {target})', f'    fit_s = timed_fit(name, model, {train}, {target})')
        code = code.replace('    fit_s = time.perf_counter() - t0\n', '')
        code = code.replace(f'    pred = model.predict({test})', f'    pred, predict_ms = timed_predict(name, model, {test})')
        return code.replace('    predict_ms = (time.perf_counter() - t0) * 1000\n', '')
    return code


def programs(tasks):
    original = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    assert len(original) == 35
    for row in original:
        contract = row['task'] in MIGRATIONS
        yield dict(row, expected_original=row['expected'], expected=False if contract else row['expected'],
                   phase='original', contract_changed=contract)
    for row in original:
        if row['task'] in MIGRATIONS:
            yield dict(row, code=migrated(row), phase='migrated', contract_changed=True)

    def pair(lesson, task, description, change, expected):
        item = tasks[lesson + '/' + task]
        return dict(lesson=lesson, task=task, description=description,
                    code=change(item['solution']), expected=expected, phase='additional')

    yield pair('ch01/exam-1', 'parse', 'constant total', lambda s: s+'\ntotal = 254542', False)
    yield pair('ch01/exam-1', 'parse', 'typed text input', lambda s:s.replace('text = ', 'text: str = ', 1), True)
    yield pair('ch01/exam-1', 'parse', 'normalization after input declaration', lambda s:s.replace('total = 0', 'text = text.strip()\ntotal = 0'), True)
    yield pair('ch01/exam-1', 'parse', 'map through lambda invoking parser', lambda s:s[:s.index('total = 0')]+'total = sum(q*p for _,q,p in map(lambda line: parse_line(line), filter(None,text.splitlines())))', True)
    yield pair('ch01/exam-1', 'parse', 'keyword argument with own parameter name', lambda s:s.replace('def parse_line(line):', 'def parse_line(row):').replace('line.split(";")', 'row.split(";")').replace('= parse_line(line)', '= parse_line(row=line)'), True)
    yield pair('ch01/exam-1', 'parse', 'lambda parser with map', lambda s: s[:s.index('total = 0')].replace('def parse_line(line):\n    city, cups, price = line.split(";")\n    return [city, int(cups), int(price)]', 'parse_line = lambda line: [line.split(";")[0], *map(int, line.split(";")[1:])]')+'total = sum(q*p for _,q,p in map(parse_line, filter(None,text.splitlines())))', True)
    yield pair('ch04/07c-metrics', 'funnel-platform', 'row permutation keeps keys', lambda s: s+'\npay_conv = pay_conv.iloc[::-1]', True)
    yield pair('ch06/04-categorical', 'shop-rate', 'whole-row sorting', lambda s: s+'\nX_train = X_train.sort_index(); X_test = X_test.sort_values("shop_id")', True)
    yield pair('ch06/04-categorical', 'shop-rate', 'missing fallback for unseen shop', lambda s: s.replace('.fillna(y_train.mean())',''), False)
    yield pair('ch07/03-threshold', 'roc-plot', 'changed substantial vertex', lambda s: s.replace('ax.plot(fpr, tpr)', 'tpr = tpr.copy(); tpr[len(tpr)//2] += .01\nax.plot(fpr, tpr)'), False)
    yield pair('ch11/04b-softmax', 'batches', 'no shuffle', lambda s: s.replace('rng.permutation(len(y))','np.arange(len(y))'), False)
    refinement = json.loads(FIXTURE.with_name('batches_20261115_refinement.json').read_text())
    yield from refinement['programs']
    yield pair('ch13/04c-llm', 'parse-llm', 'different answers swapped', lambda s: s+'\nparsed.iloc[[0,1]] = parsed.iloc[[1,0]].to_numpy()', False)
    yield pair('ch15/05-project', 'guard', 'only first violation', lambda s: s.replace('    return problems', '    return problems[:1]'), False)
    for lesson, task in [('ch10/05-project','compare'), ('ch10/06-libraries','speed-table')]:
        yield pair(lesson, task, 'seconds mistakenly saved as milliseconds', lambda s:s+'\ntable["predict_ms"] /= 1000', False)
        yield pair(lesson, task, 'measured interval shifted by constant', lambda s:s+'\ntable["fit_s"] += .01', False)
        yield pair(lesson, task, 'random intervals replace measurements', lambda s:s+'\ntable["fit_s"] = np.random.default_rng(17).uniform(.1, .3, len(table))', False)
        for slow in (False, True):
            ticks=[]
            for i in range(5 if task=='compare' else 3):
                ticks.extend([i*1000., i*1000.+(61+i if slow else .11+i*.01), i*1000.+100, i*1000.+100.002+i*.001])
            prefix='_probe_ticks=iter('+repr(ticks)+')\n_measurement_clock=lambda: next(_probe_ticks)\n'
            yield pair(lesson, task, f'deterministic registered intervals slow={slow}', lambda s,p=prefix:p+s, True)
        yield pair(lesson, task, 'own functions delegate to supplied timer',
                   lambda s:'own_fit = lambda *args: timed_fit(*args)\nown_predict = lambda *args: timed_predict(*args)\n'+s.replace('timed_fit(', 'own_fit(').replace('timed_predict(', 'own_predict('), True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--emit', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--baseline', action='store_true', help='Reproduce recorded pre-fix outcomes, including the documented defects')
    parser.add_argument('--batches-before', action='store_true', help='Reproduce the two additional false accepts before the batches refinement')
    args=parser.parse_args()
    if args.baseline and args.batches_before:
        parser.error('Choose one baseline snapshot.')
    if args.batches_before:
        snapshot=json.loads(FIXTURE.with_name('batches_20261115_refinement.json').read_text())
        task=snapshot['task_before']
        tasks={task['lesson']+'/'+task['id']:task}
        rows=[dict(r,expected_original=r['expected'],expected=r['observed_before'],phase='refinement-observed') for r in snapshot['programs']]
    elif args.baseline:
        snapshot=json.loads(FIXTURE.with_name('reaudit_20261115_tasks.json').read_text())
        tasks={t['lesson']+'/'+t['id']:t for t in snapshot['tasks']}
        original=[json.loads(line) for line in FIXTURE.read_text().splitlines()]
        observed=[json.loads(line) for line in (ROOT/'docs/course-improvements/reaudit/expert-native.jsonl').read_text().splitlines()]
        assert len(original)==len(observed)==35
        rows=[]
        for row, old in zip(original,observed):
            assert (row['lesson'],row['task'],row['description'])==(old['lesson'],old['task'],old['description'])
            rows.append(dict(row,expected_original=row['expected'],expected=old['passed'],phase='historical-observed'))
    else:
        tasks=current_tasks()
        rows=list(programs(tasks))
    if args.emit:
        args.emit.mkdir(parents=True,exist_ok=True)
        keys={r['lesson']+'/'+r['task'] for r in rows}
        (args.emit/'tasks.json').write_text(json.dumps([tasks[k] for k in sorted(keys)],ensure_ascii=False))
        (args.emit/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
        print(f'Exported {len(keys)} tasks and {len(rows)} programs to {args.emit}')
        return
    import tempfile
    from contextlib import chdir
    results=[]
    for row in rows:
        item=tasks[row['lesson']+'/'+row['task']]
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            for name in item.get('files',[]): shutil.copy(ROOT/'site/data'/name,name)
            result=harness.run(row['code'],item['check'],item.get('setup'),False)
        record=dict(row,ok=result['ok'],passed=result['check']['passed'],message=result['check']['msg'],error=result['error'],stdout=result['out'])
        results.append(record)
        print(json.dumps({k:v for k,v in record.items() if k!='code'},ensure_ascii=False),flush=True)
        if args.output: args.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
        assert result['ok'] and result['check']['passed']==row['expected'],record
    if args.batches_before:
        print('Reproduced both recorded false accepts before the batches refinement.')
    elif args.baseline:
        print('Reproduced 35 recorded historical outcomes; this includes 12 original grading mismatches.')
    else:
        print(f'PASS {len(results)} programs; 35 exact historical submissions, 7 migrations, {len(results)-42} additional probes.')

if __name__=='__main__': main()
