// Run from the course root with the exported task catalog.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const tasks = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const vendor = resolve('site/assets/vendor/pyodide') + '/'
const { loadPyodide } = await import(pathToFileURL(vendor + 'pyodide.mjs').href)
const py = await loadPyodide({indexURL: vendor})
await py.loadPackage(['numpy', 'pandas', 'scipy', 'statsmodels', 'matplotlib'], {messageCallback(){}})
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
console.log(process.version, py.version, py.runPython('import numpy, pandas, scipy, statsmodels, matplotlib; [sys.version.split()[0], numpy.__version__, pandas.__version__, scipy.__version__, statsmodels.__version__, matplotlib.__version__]').toJs())
const examples = [
    ['01-probability/running', 'reference', identity],
    ['01-probability/running', 'wrong horizontal constant', substitute('ax.axhline(0.24','ax.axhline(0.84')],
    ['02-distributions/poisson-queue', 'off by one', substitute('p_queue = round(stats.poisson.sf(3','p_queue = round(stats.poisson.sf(4')],
    ['04-confidence/bootstrap', 'reference', identity],
    ['04-confidence/bootstrap', 'valid bootstrap by index', substitute('rng.choice(t, size=len(t), replace=True)', 't[rng.integers(0, len(t), size=len(t))]')],
    ['04-confidence/bootstrap', 'incorrect 50 percent CI', substitute('[2.5, 97.5]', '[25, 75]')],
    ['04-confidence/bootstrap', 'invented narrow CI', append('lo, hi = med - 0.01, med + 0.01')],
    ['04-confidence/errorbars', 'zero uncertainties', substitute('yerr=[g["mean"] - lo, hi - g["mean"]]', 'yerr=0')],
    ['05-hypotheses/perm-snow', 'negative p and degenerate null', append('p_value = -1\ndiffs = np.zeros(3000)')],
    ['05-hypotheses/perm-fn', 'finite MC corrected', substitute('count / n_perm', '(count + 1) / (n_perm + 1)')],
    ['05-hypotheses/perm-fn', 'inverted res p', append('res = (999., -0.47)')],
    ['06-tests/agree', 'substitute asymptotic p for simulated', append('p_perm = p_z')],
    ['07-ab/ztest', 'unrounded p', append('p_value = p')],
    ['07-ab/ab-report', 'generic', identity],
    ['07-ab/ab-report', 'ignores metric name', substitute('def ab_report(df, metric):','def ab_report(df, metric):\n    metric = "ordered"')],
    ['09-project/late', 'negative p', append('p_late = -0.00001')],
    ['09-project/cities', 'all unadjusted p are one', append('by_city["p"] = 1.0')],
    ['09-project/chart', 'Wilson', identity],
    ['09-project/chart', 'zero-length Wilson whiskers', substitute('yerr=[(g["mean"] - lo) * 100, (hi - g["mean"]) * 100]', 'yerr=0')],
    ['09-project/decision', 'three outcomes', identity],
    ['09-project/decision', 'always extend', substitute('"decision": decision', '"decision": "продлить тест"')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch05/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
