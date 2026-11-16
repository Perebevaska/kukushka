// From the repository root, pass the exported JSON and optionally a scratch output folder for PNG previews.
import { readFileSync, writeFileSync } from 'node:fs'
import { resolve, join } from 'node:path'
import { pathToFileURL } from 'node:url'
const read = file => readFileSync(resolve(file),'utf8')
const tasks = JSON.parse(read(process.argv[2]))
const vendor = resolve('site/assets/vendor/pyodide') + '/'
const { loadPyodide } = await import(pathToFileURL(vendor+'pyodide.mjs').href)
const py = await loadPyodide({indexURL:vendor})
await py.loadPackage(['pandas','matplotlib'],{messageCallback(){}})
py.FS.writeFile('/home/pyodide/_dsc_harness.py',read('site/assets/harness.py'))
py.runPython('import sys; sys.path.insert(0,"/home/pyodide"); import _dsc_harness')
const run=py.pyimport('_dsc_harness').run
console.log(process.version,py.version,py.runPython('import pandas as pd, matplotlib; (sys.version.split()[0], pd.__version__, matplotlib.__version__)').toJs())
for(const [lesson,id,label,build] of [
    ['01-plots','barh','right-default',c=>c],
    ['01-plots','barh','right-inverted',c=>c.replace('.sort_values()', '.sort_values(ascending=False)')+'\nax.invert_yaxis()'],
    ['01-plots','bar-shop','wrong-labels',c=>c.replace('bar(counts.index,','bar(counts.index[::-1],')],
    ['01-plots','pandas-plot','right-accessor',c=>c.replace('plot(kind="bar",','plot.bar(')],
    ['02-histograms','hist-km','right',c=>c],
    ['02-histograms','hist-km','amount-as-km',c=>c.replace('d["distance_km"]','d["amount"]')],
    ['06-correlation','scatter','distance-vs-time',c=>c],
    ['06-correlation','scatter','reverse-variables',c=>c.replace('ok["distance_km"], ok["actual_min"]','ok["actual_min"], ok["distance_km"]')],
    ['07-readable','percent-axis','right-inverted',c=>c.replace('shares.sort_values()','shares.sort_values(ascending=False)')+'\nax.invert_yaxis()'],
    ['05b-cohorts','heat','cohort-image',c=>c],
    ['05b-cohorts','heat','fraction-instead-percent',c=>c.replace('imshow(show.values','imshow(show.values/100')],
    ['09-project','clean','wrong-delay-signed-backwards',c=>c.replace('ok["actual_min"] - ok["promised_min"]','ok["promised_min"] - ok["actual_min"]')],
    ['09-project','scale','right',c=>c],
    ['09-project','scale','absolute-time-instead-delay',c=>c.replace('ax.hist(ok["delay"]','ax.hist(ok["actual_min"]')],
    ['09-project','walkers','right-reference',c=>c],
    ['09-project','walkers','correct-order-walkers-first',c=>c+'\npv = pv[["пеший","вело","авто"]]'],
    ['09-project','walkers','wrong-labels',c=>c+'\npv.columns = pv.columns[::-1]'],
    ['09-project','weekly','right',c=>c],
    ['09-project','weekly','flat-meaningless-chart',c=>c.replace('weeks.plot(ax=ax','(weeks*0).plot(ax=ax')],
    ['09-project','report','reference-one-day',c=>c+'\ndelivery_report(raw[raw.created.dt.strftime("%Y-%m-%d") == "2026-10-07"])'],
    ['07-readable','small-multiples','six-case-panels',c=>c],
]) {
    const t=tasks.find(v=>v.lesson==='ch04/'+lesson && v.kind==='task' && v.id===id)
    for(const f of t.files)py.FS.writeFile(f,readFileSync(resolve('site/data',f)))
    const r=run(build(t.solution),t.check,t.setup,true)
    const out=r.toJs({dict_converter:Object.fromEntries})
    r.destroy()
    console.log(lesson,id,label,out.check?.passed??false,out.error?.text??out.check?.msg??'')
    if(process.argv[3] && out.figs[0])writeFileSync(join(process.argv[3],lesson+'-'+id+'-'+label+'.png'),Buffer.from(out.figs[0],'base64'))
}
