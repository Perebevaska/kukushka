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
    ['03b-money-threshold/honest-t', 'validation optimum', identity],
    ['03b-money-threshold/honest-t', 'test optimum', substitute('vals = [profit(y_val, p_val, t)', 'vals = [profit(y_test, p_test, t)')],
    ['03-threshold/roc-plot', 'correct plotted lines', identity],
    ['03-threshold/roc-plot', 'false diagonal has interior (0.5,0.9)', substitute('ax.plot([0, 1], [0, 1]', 'ax.plot([0, .5, 1], [0, .9, 1]')],
    ['06b-feature-check/combo', 'scale separately in every fold', substitute(
        'Xs = StandardScaler().fit_transform(X_train)\n    return cross_val_score(LogisticRegression(max_iter=2000), Xs',
        'from sklearn.pipeline import make_pipeline\n    return cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), X_train')],
    ['07b-own-steps/group-ratio', 'learned training statistics', identity],
    ['07b-own-steps/group-ratio', 'learn group means again at transform', substitute('base = X[self.by].map(self.means_).fillna(self.overall_)', 'base = X.groupby(self.by)[self.col].transform("mean")')],
    ['09-project/pipe', 'trained preprocessing', identity],
    ['09-project/pipe', 'correct name-based columns, different order', substitute('X_train, X_test, y_train, y_test =', 'X = X.sort_index(axis=1)\nX_train, X_test, y_train, y_test =')],
    ['09-project/pipe', 'no preprocessing step despite reported scores', append('pipe.set_params(prep="passthrough")')],
    ['09-project/metric', 'stable sort as alternative to nlargest', substitute('s.nlargest(int(len(s) * share))', 's.sort_values(ascending=False, kind="stable").head(int(len(s) * share))')],
    ['09-project/metric', 'bottom risk', substitute('s.nlargest', 's.nsmallest')],
    ['09-project/grid', 'reported table contains all zero scores', append('res["mean_test_score"] = 0')],
    ['09-project/final', 'compare exact count selected by the rule', substitute('round(catch_rate(y_test, scores, share=rule_share_test), 3)', 'round(y_test.iloc[scores.argsort()[::-1][:int(rule.sum())]].sum() / y_test.sum(), 3)')],
    ['08-tuning/save-load', 'normal round trip', identity],
    ['08-tuning/save-load', 'saved artifact is empty', append('open("churn_model.joblib", "wb").close()')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch07/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
