// Run from the course root with the exported task catalog.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const tasks = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const vendor = resolve('site/assets/vendor/pyodide') + '/'
const { loadPyodide } = await import(pathToFileURL(vendor + 'pyodide.mjs').href)
const py = await loadPyodide({indexURL: vendor})
await py.loadPackage(['numpy', 'pandas', 'scipy', 'scikit-learn', 'matplotlib'], {messageCallback(){}})
py.FS.writeFile('/home/pyodide/_dsc_harness.py', readFileSync('site/assets/harness.py'))
py.runPython('import sys; sys.path.insert(0,"/home/pyodide"); import _dsc_harness')
const run = py.pyimport('_dsc_harness').run
const identity = c => c
const append = code => c => c + '\n' + code
function substitute(before, after) {
    return code => {
        if (!code.includes(before)) throw new Error(before)
        return code.replace(before, after)
    }
}
console.log(process.version, py.version, py.runPython('import numpy, pandas, scipy, sklearn, matplotlib; [sys.version.split()[0], numpy.__version__, pandas.__version__, scipy.__version__, sklearn.__version__, matplotlib.__version__]').toJs())
const examples = [
    ['01-artifact/decide','reference',identity],
    ['01-artifact/decide','same comparison with threshold on the left',substitute('p >= card["threshold"]','card["threshold"] <= p')],
    ['01-artifact/decide','reverse threshold',substitute('p >= card["threshold"]','p < card["threshold"]')],
    ['02-service/validate','reference range validator',identity],
    ['02-service/validate','allow invalid upper share',substitute('0 <= v <= 1','0 <= v <= 100')],
    ['02b-service-run/tests-write','correct alternative boundary cases',append('cases.append(("нулевая доставка", dict(GOOD,delivery_share=0),200))')],
    ['02b-service-run/tests-write','omit boolean regression',append('cases.pop(1)')],
    ['03-experiments/paired','correct reversed operands',substitute('diff = rf - lr','diff = -(lr-rf)')],
    ['03-experiments/paired','reverse difference',substitute('diff = rf - lr','diff = lr - rf')],
    ['04-deploy/cron-match','reference + two dates satisfying real cron',append('print(cron_match("0 0 1 * 1",datetime(2026,11,2)),cron_match("0 0 1 * 1",datetime(2026,11,1)))')],
    ['04-deploy/cron-match','drop weekday filter',substitute('and field_match(dow, dt.isoweekday() % 7)','and True')],
    ['05-project/slow','reference figure',identity],
    ['05-project/slow','remove all latency observations and the SLA line from figure',append('ax.clear()')],
    ['05-project/kopecks','model aggregate units alternative',substitute('round(check_by_client["app 3.2"] / check_by_client["app 3.1"])','int(round(check_by_client.loc["app 3.2"] / check_by_client.loc["app 3.1"]))')],
    ['05-project/kopecks','invert rubles/kopecks',substitute('round(check_by_client["app 3.2"] / check_by_client["app 3.1"])','round(check_by_client["app 3.1"] / check_by_client["app 3.2"])')],
    ['06-final-project/target','correct calendar offset',substitute('pd.offsets.MonthEnd(months)','pd.offsets.MonthEnd(n=months)')],
    ['06-final-project/target','old off-by-one DateOffset',substitute('pd.offsets.MonthEnd(months)','pd.DateOffset(months=months)')],
    ['06-final-project/target','shuffle real labels among client IDs; small synthetic fixture intact',substitute('left.astype(int).values','(left.astype(int).shift(1, fill_value=left.iloc[-1]) if len(left)>10 else left.astype(int)).values')],
    ['06-final-project/features','reference features',identity],
    ['06-final-project/models','reference grouped AUC in WASM',identity],
    ['06-final-project/features','post-check mutation: return all NaNs for actual office features',append('original=order_features\ndef order_features(cutoff): return original(cutoff)*float("nan")')],
    ['06-final-project/package','reference package',identity],
    ['06-final-project/package','wrong CRM city for every call',append('out["city"]="Несуществующий город"\nout.to_csv("call_list.csv",index=False)')],
    ['06-final-project/package','wrong CRM ID for every call',append('out["client_id"]="C0"\nout.to_csv("call_list.csv",index=False)')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch15/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, String(out.error?.text ?? out.check?.msg ?? '').slice(0,205))
    if (key.includes("cron-match")) console.log("cron witness",out.out)
    if (key.endsWith("/models")) console.log("grouped AUC",out.out)
}
