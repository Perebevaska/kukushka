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
    ['02-budget/gains-plot','correct curves',identity],
    ['02-budget/gains-plot','constant at the 60th point',substitute('ax.plot(share, caught,', 'ax.plot(share, np.repeat(caught[59], len(caught)),')],
    ['04b-segments/report-text','correct report',identity],
    ['04b-segments/report-text','wrong conclusion, same numeric tokens',append('report = report + " Значит, модель совершенно бесполезна: ROC-AUC ниже 0.50."')],
    ['05b-fairness/missed','author counts in bundled runtime',append('print(missed_n, missed_share.to_dict())')],
    ['06-project/decision','correct maximum acceptable mean',identity],
    ['06-project/decision','globally highest mean, ignores risk',c => c.replace('choice = ok["mean"].idxmax()', 'choice = risk["mean"].idxmax()').replace('ok.loc[choice, "mean"]','risk.loc[choice, "mean"]')],
    ['06-project/decision','equivalent descending sort',substitute('choice = ok["mean"].idxmax()', 'choice = ok.sort_values("mean", ascending=False).index[0]')],
    ['07-final-project/fp-features','original named placeholder',identity],
    ['07-final-project/fp-features','valid SQLite named placeholder :as_of',substitute(':cutoff',':as_of')],
    ['07-final-project/fp-features','assign risk features to wrong guests',append('agg["morning_share"] = agg["morning_share"].to_numpy()[::-1]')],
    ['07-final-project/fp-curve','original thresholds',identity],
    ['07-final-project/fp-curve','wrong comparator at exact probability',substitute('send = p > t','send = p >= t')],
    ['07-final-project/fp-curve','ignores caller margin and cost',substitute('value * tp - cost * int(send.sum())','1600 * tp - 150 * int(send.sum())')],
    ['07-final-project/fp-honest','incremental policy',identity],
    ['07-final-project/fp-honest','ignores counterfactual when choosing strategy',substitute('"margin": 1600 * ((send & (y_train == 1)).sum() - r_t * send.sum())','"margin": 1600 * (send & (y_train == 1)).sum()')],
    ['07-final-project/fp-honest','omits organic purchases from final return',append('honest_profit = naive_profit')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch08/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    let source = mutate(t.solution)
    if (label.includes(':as_of')) source = t.solution.replaceAll(':cutoff', ':as_of').replace('{"cutoff": CUTOFF}', '{"as_of": CUTOFF}')
    await py.loadPackagesFromImports([t.setup, source, t.check].join("\n"), {messageCallback(){}})
    const result = run(source, t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    if (key === "05b-fairness/missed") console.log(out.out.trim())
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
