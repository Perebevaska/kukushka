import { readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const root = process.cwd();
const base = 'docs/reaudit-2026-11-16/ch04';
const read = path => readFileSync(path, 'utf8');
const tasks = JSON.parse(read('site/notebooks/tasks/ch04.json')).tasks;
const known = JSON.parse(read(base + '/check-evidence/probes-before.json')).filter(p => p.case !== 'empty-answer');
const cases = [];
function derive(id, task, example, change, expected) {
    const original = known.find(p => p.task === task && p.case === example);
    cases.push({...original, case: id, code: change(original.code), expected});
}
derive('visible-left-title', 'title', 'alternative-format-string', s => s.replace('int(m.iloc[0])))', 'int(m.iloc[0])), loc="left")'), true);
derive('reverse-drawing-invert-axis', 'labeled', 'alternative-aggregate', s => s.replace('ax.bar(rev.index, rev.values)', 'ax.bar(rev.index[::-1], rev.values[::-1])\nax.invert_xaxis()'), true);
derive('misleading-all-numeric-labels', 'labeled', 'alternative-aggregate', s => s.replace('ax.bar_label(bars)', 'ax.bar_label(bars, labels=["0"] * len(bars))'), false);
derive('correct-step-histogram', 'five-min', 'alternative-explicit-edges', s => s.replace('bins=range', 'histtype="step", bins=range'), true);
derive('correct-stepfilled-density', 'compare', 'alternative-reverse-group-order', s => s.replace('density=True', 'histtype="stepfilled", density=True'), true);
derive('explicit-legend-artist-handles', 'compare', 'alternative-reverse-group-order', s => s.replace('for c in', 'handles=[]\nfor c in').replace('    ax.hist(', '    heights, edges, bars = ax.hist(').replace('alpha=0.5, label=c)', 'alpha=0.5)\n    handles.append(bars[0])').replace('ax.legend()', 'ax.legend(handles, ["авто", "вело"])'), true);
function variant(id, basis, change, expected) {
    const original = cases.find(p => p.case === basis);
    cases.push({...original, case:id, code:change(original.code), expected});
}
variant('wrong-left-title', 'visible-left-title', s => s.replace('int(m.iloc[0])', 'int(m.iloc[0])+1'), false);
variant('reversed-visually-ascending', 'reverse-drawing-invert-axis', s => s.replace('ax.invert_xaxis()', ''), false);
variant('wrong-step-frequencies', 'correct-step-histogram', s => s.replace('ax.hist(t,', 'ax.hist(t+5,'), false);
variant('wrong-stepfilled-second-group', 'correct-stepfilled-density', s => s.replace('ax.hist(t,', 'ax.hist(t + (3 if c=="авто" else 0),'), false);
variant('explicit-legend-swapped-handles', 'explicit-legend-artist-handles', s => s.replace('ax.legend(handles,','ax.legend(handles[::-1],'), false);
derive('separate-artist-labels', 'labeled', 'alternative-aggregate', s => s.replace('ax.bar_label(bars)', 'for bar, value in zip(bars, rev.values):\n    ax.text(bar.get_x()+bar.get_width()/2, value, f"{value:,.0f}".replace(",", " "), ha="center", va="bottom")'), true);
derive('labels-on-wrong-bars', 'labeled', 'alternative-aggregate', s => s.replace('ax.bar_label(bars)', 'ax.bar_label(bars, labels=rev.values[::-1])'), false);
derive('fractional-daily-counts', 'ufa-empty', 'alternative-reordered-keyed-days', s => s+'\nper_day=per_day+0.25\nempty=empty+0.25', false);
derive('fractional-courier-counts', 'slow', 'alternative-whole-deliveries-reordered', s => s+'\nslow_by={k:v+.5 for k,v in slow_by.items()}', false);
derive('fractional-guest-totals', 'age', 'alternative-whole-rows-columns-reordered', s => s+'\njan_m3+=.25\ntotal_m0+=.25', false);
derive('fractional-cleaning-log', 'clean', 'alternative-whole-deliveries-reordered', s => s+'\nlog={k:v+.5 for k,v in log.items()}', false);
derive('count-nonmissing-instead-of-group-size', 'slice-fn', 'alternative-aggregate-columns', s => s.replace('n=(col,"size")','n=(col,"count")'), false);
derive('same-named-columns-reordered', 'slice-fn', 'alternative-aggregate-columns', s => s.replace('return t.sort_values','return t[["mean","n"]].sort_values'), true);
const oldReport = read(base + '/student/own_report_code.py');
const fixedReport = oldReport.replace('s=ok[(ok.courier=="пеший")', 'leader=ok.groupby("courier",sort=True).late.mean().idxmax()\n    s=ok[(ok.courier==leader)');
for(const [id, code, expected] of [
 ['alternative-report', fixedReport, true],
 ['fixed-walkers', oldReport, false],
 ['zero-for-no30',fixedReport.replace('promise=None if s.empty','promise=0 if s.empty'),false],
 ['first-input-tie',fixedReport.replace('groupby("courier",sort=True)','groupby("courier",sort=False)'),false],
]) cases.push({lesson:'09-project',task:'report',case:id,code,expected});
const wauCode=`import pandas as pd
orders = pd.read_csv("preorders.csv", parse_dates=["date"])
calendar = pd.DataFrame({"date":pd.date_range("2026-01-01", "2026-06-30")})
calendar["week"] = calendar.date.dt.to_period("W")
orders["week"] = orders.date.dt.to_period("W")
weekly = calendar.groupby("week").size().to_frame("days").join(orders.groupby("week").guest_id.nunique().rename("wau")).fillna(0)
full = weekly.loc[weekly.days.eq(7)].copy()
n_full, min_wau = len(full), full.wau.min()`;
const emptyWeek=`import pandas as pd
src=pd.read_csv("preorders.csv")
src.loc[~src.date.between("2026-01-05","2026-01-11")].to_csv("preorders.csv",index=False)`;
for(const [id, code, expected] of [
 ['week-without-orders-counts-seven-days',wauCode,true],
 ['week-without-orders-wrong-days',wauCode+'\nweekly.loc[weekly.wau.eq(0), "days"]=0',false],
 ['weekly-right-full-wrong',wauCode+'\nfull=full.copy();full.loc[full.wau.eq(0),"wau"]=1',false]
]) cases.push({lesson:'05c-dau-mau',task:'wau-full',case:id,prepare:emptyWeek,code,expected});
cases.push(...known);
const vendor=root+'/site/assets/vendor/pyodide/';
const { loadPyodide } = await import(pathToFileURL(vendor+'pyodide.mjs'));
const py=await loadPyodide({indexURL:vendor});
await py.loadPackage(['pandas','matplotlib','scipy']);
py.FS.writeFile('/home/pyodide/_dsc_harness.py',read('site/assets/harness.py'));
py.runPython('import sys;sys.path.insert(0,"/home/pyodide");import _dsc_harness');
const run=py.pyimport('_dsc_harness').run;
const results=[];
for (const p of cases) {
  const task=tasks['ch04/'+p.lesson+'/'+p.task];
  for(const file of task.files) py.FS.writeFile('/home/pyodide/'+file,readFileSync('site/data/'+file));
  if(p.prepare) py.runPython(p.prepare);
  const result=run(p.code,task.check,task.setup||null,false);
  const r=result.toJs({dict_converter:Object.fromEntries}); result.destroy();
  const actual=!!r.check?.passed;
  const row={id:p.lesson+'/'+p.task,case:p.case,expected:p.expected,actual,feedback:r.check?.msg??r.error?.text??null,code:p.code,prepare:p.prepare||null};
  results.push(row);
  console.log(row.id,row.case,p.expected,actual,row.feedback);
}
writeFileSync(process.argv[2]||base+'/fixes/review-results.json',JSON.stringify(results, null, 2)+'\n');
const mismatches=results.filter(row => row.expected !== row.actual);
console.log('Expected verdicts:',results.length-mismatches.length,'/',results.length);
if(mismatches.length) process.exitCode=1;
