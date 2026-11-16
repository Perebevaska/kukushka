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
    ['02-backprop/grad-check', 'centered difference and analytic gradient', identity],
    ['02-backprop/grad-check', 'incorrect gradient sign', substitute('sigmoid(z) - y','y - sigmoid(z)')],
    ['02b-graph/clip-norm', 'equivalent L2 magnitude', substitute('np.linalg.norm(g)', 'np.sqrt(np.dot(g, g))')],
    ['02b-graph/clip-norm', 'clip coordinate by coordinate', substitute('g * (max_norm / n)', 'np.clip(g, -max_norm, max_norm)')],
    ['04b-softmax/softmax','scipy implementation',substitute('P = softmax(Z)','from scipy.special import softmax as sm\nP = sm(Z, axis=1)')],
    ['04b-softmax/softmax','exponential overflow',substitute('Z = Z - Z.max(axis=1, keepdims=True)','Z = Z.copy()')],
    ['04b-softmax/batches','valid permutation',identity],
    ['04b-softmax/batches','never shuffle',substitute('rng.permutation(len(y))','np.arange(len(y))')],
    ['04c-debug/dropout','inverted mask',identity],
    ['04c-debug/dropout','omitted scale',substitute('H * mask / (1 - rate)','H * mask')],
    ['04c-debug/batchnorm','unbiased running var like PyTorch',substitute('momentum * var','momentum * Xb.var(axis=0, ddof=1)')],
    ['05-project/look','no digit images on axes',substitute('ax.imshow(mean_imgs[k], cmap="gray_r")','pass')],
    ['05-project/mlp','reference probabilities',identity],
    ['05-project/mlp','uniform model scores',substitute('proba = model.predict_proba(X_test)','proba = np.full((len(X_test), 10), .1)')],
    ['05-project/mlp','negative probabilities',append('proba[:, :] = 0; proba[:, 0] = -1; proba[:, 1] = 2')],
    ['05-project/errors','equivalent boolean counts',substitute('(review & errors).sum() / errors.sum()','review[errors].mean()')],
    ['05-project/errors','fraction errors among sent instead',substitute('(review & errors).sum() / errors.sum()','errors[review].mean()')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch11/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, out.error?.text ?? out.check?.msg ?? '')
}
console.log('Pyodide project counts: label correct, sent, errors sent, maximum probabilities for sent', py.runPython(`
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_digits
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
x,y = load_digits(return_X_y=True)
a,b,c,d = train_test_split(x/16, y,test_size=.25,random_state=42,stratify=y)
summary=[]
for model in (KNeighborsClassifier(n_neighbors=3), MLPClassifier(hidden_layer_sizes=(64,),alpha=.001,max_iter=500,random_state=0)):
    pr = model.fit(a,c).predict_proba(b)
    err = pr.argmax(1) != d
    send=pr.max(1)<.9
    summary.append((model.__class__.__name__,int((~err).sum()),int(send.sum()),int((err & send).sum()),str(np.unique(pr.max(1)[send]).round(3)) if model.__class__.__name__.startswith('KNeighbors') else ''))
summary
`).toJs())
