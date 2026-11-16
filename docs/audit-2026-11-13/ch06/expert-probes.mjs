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
    ['04-categorical/new-orders', 'correct new weather', identity],
    ['04-categorical/new-orders', 'new weather assigned snow', append('X_new.loc[0,"weather_снег"] = 1')],
    ['04-categorical/shop-rate', 'training self-target included', identity],
    ['04-categorical/shop-rate', 'leave-one-out training encoding', append('sizes = X_train.groupby("shop_id").shop_id.transform("size")\nX_train["shop_rate"] = (X_train.shop_rate * sizes - y_train.astype(int)) / (sizes - 1)')],
    ['07-regression/fact-pred', 'matched rows', identity],
    ['07-regression/fact-pred', 'reverse both, valid order', substitute('scatter(pred, y_test,','scatter(pred[::-1], y_test.iloc[::-1],')],
    ['07-regression/fact-pred', 'reverse only observed times', substitute('scatter(pred, y_test,','scatter(pred, y_test.iloc[::-1],')],
    ['08b-groups-speed/group-split', 'group holdout', identity],
    ['08b-groups-speed/group-split', 'ordinary split row count', append('n_test_rows = len(g_te)')],
    ['09-project/prepare', 'correct split', identity],
    ['09-project/prepare', 'equivalent alphabetic feature order', substitute('X_train, X_test, y_train, y_test =', 'X = X.sort_index(axis=1)\nX_train, X_test, y_train, y_test =')],
    ['09-project/prepare', 'target smuggled as days_since_last', substitute('X_train, X_test, y_train, y_test =', 'X["days_since_last"] = y\nX_train, X_test, y_train, y_test =')],
    ['09-project/prepare', 'train labels shuffled in place', append('y_train = y_train.sample(frac=1, random_state=3).to_numpy()')],
    ['09-project/final', 'train-only reference', identity],
    ['09-project/final', 'refit model on test after calculating scores', append('model.fit(X_test, y_test)')],
    ['09-project/top', 'correct ranking', identity],
    ['09-project/top', 'equivalent stable ranking', substitute('risk.nlargest(60)', 'risk.sort_values(ascending=False, kind="stable").head(60)')],
    ['09-project/top', 'overwritten top contains lowest risk', append('top = risk.nsmallest(60)')],
    ['09-project/top', 'incorrect IDs', append('top_ids = top_ids[::-1]')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch06/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
