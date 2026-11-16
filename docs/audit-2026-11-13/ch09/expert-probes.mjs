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
    ['02-matrices/gram','correct full matrix',identity],
    ['02-matrices/gram','use NumPy Gram and covariance shortcuts',substitute('C = Xc.T @ Xc / (n - 1)', 'C = np.cov(X, rowvar=False)')],
    ['02-matrices/gram','zero out Gram matrix',append('G = np.zeros_like(G)')],
    ['02b-vectorize/vectorize','reference loop and vectorized algorithm',identity],
    ['02b-vectorize/vectorize','call the exact loop twice and fabricate speedup',c => {
        c = substitute('b = pay_vec(km, rain)','pay_vec = pay_loop\nb = pay_vec(km, rain)')(c)
        return c + '\nt_loop, t_vec, speedup = 1., .01, 100.'
    }],
    ['03-normal-equation/my-ols','stable direct least squares',substitute('np.linalg.solve(X1.T @ X1, X1.T @ y)', 'np.linalg.lstsq(X1, y, rcond=None)[0]')],
    ['03-normal-equation/many-solutions','least squares solution',identity],
    ['03-normal-equation/many-solutions','two zero-fit-equivalent non-optimal weight vectors',substitute('np.linalg.lstsq(full, y, rcond=None)[0]', 'np.zeros(full.shape[1])')],
    ['03b-own-model/my-class','train via least squares on the original matrix',substitute('np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))','np.linalg.lstsq(X1, y, rcond=None)[0]')],
    ['03b-own-model/my-class','predict without intercept',substitute(' @ self.coef_ + self.intercept_',' @ self.coef_')],
    ['05-project/key','inverse-free reconstruction',substitute('hidden @ np.linalg.inv(P)', 'np.linalg.solve(P.T, hidden.T).T')],
    ['05-project/hidden-quality','fit open model only',c => c.replace('fit(X_train @ P, y_train)', 'fit(X_train, y_train)').replace('predict(X_test @ P)', 'predict(X_test)')],
    ['05-project/hidden-quality','reference holdout',identity],
    ['05-project/attack','indirect least squares attack',substitute('np.linalg.solve(known, hidden[:4])','np.linalg.lstsq(known, hidden[:4], rcond=None)[0]')],
    ['05-project/attack','restoration matrix replaced with zeros after score',append('restored = np.zeros_like(X)')],
    ['05-project/attack','false degree of disclosure',append('leaked = 0')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch09/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
