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
    ['01-text-prep/tokenize','reference',identity],
    ['01-text-prep/tokenize','drop ё',substitute('[а-яё]+','[а-я]+')],
    ['02-tfidf/idf-by-hand','equivalent log ratio',substitute('np.log((1 + n) / (1 + df_word))', '(np.log1p(n) - np.log1p(df_word))')],
    ['02-tfidf/idf-by-hand','omit smoothing',substitute('np.log((1 + n) / (1 + df_word))','np.log(n / df_word)')],
    ['02-tfidf/train-only','replace sparse test features with zeros',append('X_test = X_test.multiply(0)')],
    ['03b-labels/kappa','replace chance-corrected score with agreement',substitute('return (p_o - p_e) / (1 - p_e)','return p_o')],
    ['04b-transformers/masked-pool','broadcast mask',identity],
    ['04b-transformers/masked-pool','einsum masking',substitute('(H * mask[:, :, None]).sum(axis=1)','np.einsum("btd,bt->bd", H, mask)')],
    ['04b-transformers/masked-pool','include pads in denominator',substitute('mask.sum(axis=1, keepdims=True)','H.shape[1]')],
    ['04c-llm/parse-llm','reference parser',identity],
    ['04c-llm/parse-llm','ignore future inputs after table produced',append('def parse(answer): return {"ok": True, "topic": "цена", "sentiment": "positive"}')],
    ['04c-llm/llm-same','paired counts',identity],
    ['04c-llm/llm-same','increment both paired counts',append('llm_only += 1; model_only += 1')],
    ['05-project/score','store original shops',identity],
    ['05-project/score','put every review at the same shop',append('n["shop_id"] = "KZN-2"')],
    ['05-project/score','attach dates and original text in reverse',append('n["date"] = n["date"].iloc[::-1].to_numpy(); n["text"] = n["text"].iloc[::-1].to_numpy()')],
    ['05-project/score','reverse class probabilities',substitute('predict_proba(n["text"])[:, 1]','predict_proba(n["text"])[:, 0]')],
    ['05-project/why','reference quotes',identity],
    ['05-project/why','five manufactured quotes',append('quotes=["жалоба"]*5')],
    ['05-project/adjust','reference correction',identity],
    ['05-project/adjust','incorrect denominator sign',substitute('(tpr - fpr)','(tpr + fpr)')],
]
for (const [key, label, mutate] of examples) {
    const t = tasks.find(x => x.kind === 'task' && x.lesson + '/' + x.id === 'ch13/' + key)
    for (const f of t.files) py.FS.writeFile(f, readFileSync(resolve('site/data', f)))
    const result = run(mutate(t.solution), t.check, t.setup, true)
    const out = result.toJs({dict_converter:Object.fromEntries})
    result.destroy()
    console.log(key, label, !!out.check?.passed, String(out.error?.text ?? out.check?.msg ?? '').slice(0,200))
}
