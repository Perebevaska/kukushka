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
    ['02-filters/pool','reference max/min window axes',identity],
    ['02-filters/pool','use min pooling',substitute('.max(axis=(2, 4))','.min(axis=(2, 4))')],
    ['04-cnn/out-size','explicit floor equivalent',substitute('(n + 2 * pad - k) // stride + 1','int((n + 2 * pad - k) / stride) + 1')],
    ['04-cnn/out-size','incorrect same-output shape',substitute('2 * pad','0 * pad')],
    ['04c-detection/iou','reference',identity],
    ['04c-detection/iou','ignore box separation along x',substitute('max(0, w) * max(0, h)','abs(w) * max(0, h)')],
    ['05-project/light','empty figure with no requested brightness line',substitute('ax = bright.plot(figsize=(9, 3), marker=".")','fig, ax = plt.subplots()')],
    ['05-project/fix','reference normalization and fit',identity],
    ['05-project/fix','swap wrong product classes while preserving aggregate quality',append('wrong = (pred_norm != yD) & (pred_norm != 0)\nfor i in np.flatnonzero(wrong): pred_norm[i] = next(c for c in (1,2,3) if c not in (yD[i], pred_norm[i]))')],
    ['05-project/hours','saved correct occupancy table',identity],
    ['05-project/hours','drop time and metadata correspondence',append('df["time"]="07:00"; df["slot"]=0; df["true"]=0')],
    ['05-project/alerts','correct first alert per detected run',identity],
    ['05-project/alerts','send duplicate alerts',append('alerts=pd.concat([alerts,alerts.iloc[:1]],ignore_index=True)')],
    ['05-project/restock','equivalent mean interval occupancy',substitute('(m["true"] == 0).sum() * 0.25','(m["true"] == 0).mean() * len(m) / 4')],
    ['05-project/restock','treat readings as hours',substitute('saved_hours = (m["true"] == 0).sum() * 0.25','saved_hours = (m["true"] == 0).sum()')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch14/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, String(out.error?.text ?? out.check?.msg ?? '').slice(0,205))
    if (key === "05-project/fix" && mutate === identity) console.log("Pyodide normalized day/evening accuracy, evening empty recall/precision",out.out)
}
