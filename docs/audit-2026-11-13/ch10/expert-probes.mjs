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
    ['02-gd-many/grad-vec','analytic gradient',identity],
    ['02-gd-many/grad-vec','sum per-observation gradients',substitute('2 / len(y) * X1.T @ (X1 @ w - y)','2 * np.mean((X1 @ w - y)[:, None] * X1, axis=0)')],
    ['02-gd-many/grad-vec','reversed gradient',substitute('(X1 @ w - y)','(y - X1 @ w)')],
    ['02b-optimizers/adam-step','bias-corrected',identity],
    ['02b-optimizers/adam-step','first moment left uncorrected',substitute('m_hat = m / (1 - b1 ** t)','m_hat = m')],
    ['05-project/split','correct chronological mask',identity],
    ['05-project/split','use future revenue under weather column',append('X["temp"] = s["revenue_k"]')],
    ['05-project/split','reversed membership with correct counts',append('tr = ~tr')],
    ['05-project/split','same cutoff as boolean expression',substitute('tr = s["date"] < "2025-07-01"','tr = s["date"].lt(pd.Timestamp("2025-07-01"))')],
    ['05-project/trend','reference trend correction',identity],
    ['05-project/trend','equivalent logarithmic subtraction',substitute('(y / trend)[tr]', 'np.exp(np.log(y[tr]) - np.log(trend[tr]))')],
    ['05-project/trend','zero predicted vector after scoring',append('p_after = np.zeros_like(p_after)')],
    ['05-project/compare','reference quality and time',identity],
    ['05-project/compare','fabricated duration in every table row',append('table["fit_s"] = 0.7\ntable["predict_ms"] = 10\nnightly_ok = True')],
    ['06-libraries/speed-table','original native-like table',identity],
    ['06-libraries/speed-table','fabricated best speed winner',append('table["fit_s"] = 0.01\nfastest_fit = table.index[0]')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch10/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
