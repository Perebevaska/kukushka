// Run from the course root with the exported task catalog.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const tasks = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const vendor = resolve('site/assets/vendor/pyodide') + '/'
const { loadPyodide } = await import(pathToFileURL(vendor + 'pyodide.mjs').href)
const py = await loadPyodide({indexURL: vendor})
await py.loadPackage(['numpy', 'pandas', 'scipy', 'scikit-learn', 'matplotlib', 'statsmodels'], {messageCallback(){}})
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
    ['02-decompose/adf','default reference ADF',identity],
    ['02-decompose/adf','reversed p-value rule',substitute('if v < 0.05','if v > 0.05')],
    ['03-features/make-features','equivalent rolling then lag',substitute('s.shift(1).rolling(24).mean()','s.rolling(24).mean().shift(1)')],
    ['03-features/make-features','current outcome in window',substitute('s.shift(1).rolling(24).mean()','s.rolling(24).mean()')],
    ['03-features/leak-test','reference current-target perturbation',identity],
    ['03-features/leak-test','hardcode observed leak names for every input',append('def leak_test(features,s,t): return leaking')],
    ['03b-time-split/check-order','reference order',identity],
    ['03b-time-split/check-order','compare first dates only',substitute('X_tr.index.max() < X_te.index.min()','X_tr.index.min() < X_te.index.min()')],
    ['04-forecast/metrics','RMSE via normalized L2',substitute('np.sqrt(((fact - pred) ** 2).mean())','np.linalg.norm(fact-pred) / np.sqrt(len(fact))')],
    ['04-forecast/metrics','forecast in WAPE denominator',substitute('/ fact.sum()', '/ pred.sum()')],
    ['05-project/split','reference split',identity],
    ['05-project/split','exchange equal-size July and August',append('valid, test = test, valid')],
    ['05-project/split','current orders in a lag',append('X["lag_48"] = y')],
    ['05-project/split','equivalent dates',substitute('df.index < "2026-07-01"','df.index <= pd.Timestamp("2026-06-30 23:00")')],
    ['05-project/grid','wrong KFold',substitute('cv=TimeSeriesSplit(n_splits=3)','cv=3')],
    ['05-project/grid','TimeSeriesSplit with a safety gap',substitute('cv=TimeSeriesSplit(n_splits=3)','cv=TimeSeriesSplit(n_splits=3, gap=28)')],
    ['05-project/final','false predictions',append('pred_test = np.zeros_like(pred_test)')],
    ['05-project/staffing','reference plan',identity],
    ['05-project/staffing','incorrect saved needed vector',append('needed = np.ones_like(needed)')],
    ['05-project/staffing','floor capacity instead of ceiling',substitute('np.ceil(p / 6)','np.floor(p / 6)')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch12/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, String(out.error?.text ?? out.check?.msg ?? '').slice(0,240))
}
