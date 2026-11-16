import { readFileSync, writeFileSync, appendFileSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const root = resolve(dir, "../../../../..");
const phase = process.argv[2];
const evidence = resolve(dir, "../../check-evidence");
const {tasks, cases} = JSON.parse(readFileSync(resolve(dir, phase+"-cases.json")));
const vendor = resolve(root, "site/assets/vendor/pyodide")+"/";
const {loadPyodide} = await import(pathToFileURL(vendor+"pyodide.mjs"));
const py = await loadPyodide({indexURL:vendor});
await py.loadPackage(["scikit-learn","matplotlib","pandas"],{messageCallback(){}});
py.FS.writeFile("/home/pyodide/harness.py",readFileSync(resolve(root,"site/assets/harness.py")));
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import harness');
py.runPython(`import time as _audit_time
from sklearn.tree import DecisionTreeClassifier as _audit_tree
from sklearn.ensemble import RandomForestClassifier as _audit_forest
from sklearn.linear_model import LogisticRegression as _audit_logit
def _audit_timer_methods():
    return (_audit_time.perf_counter, *(getattr(cls,name) for cls in (_audit_tree,_audit_forest,_audit_logit) for name in ("fit","predict")))`);
const run = py.pyimport("harness").run;
const baseline = resolve(evidence,"data-baseline");
const data = ["before","baseline","timer"].includes(phase)?baseline:resolve(root,"site/data");
const files = readdirSync(baseline).filter(k=>k.endsWith(".csv"));
const log = resolve(dir,phase+"-web.jsonl");
writeFileSync(log, JSON.stringify({phase,pyodide:py.version,python:py.runPython("sys.version")})+"\n");
for (const c of cases) {
    for (const f of files) {
        const src = c.file_variants?.[f] ? resolve(evidence,c.file_variants[f]) : resolve(data,f);
        py.FS.writeFile("/home/pyodide/"+f,readFileSync(src));
    }
    const t=tasks[c.key].web;
    py.runPython("_audit_originals=_audit_timer_methods()");
    const r=run(c.code,t.check,t.setup+"\n"+(c.setup_append||""),false);
    const obj=r.toJs({dict_converter:Object.fromEntries});r.destroy();
    const restored=py.runPython("all(a is b for a,b in zip(_audit_originals,_audit_timer_methods()))");
    if (!restored || (["after","extra"].includes(phase) && obj.check.passed!==c.expected)) throw new Error(c.id+": "+obj.check.msg);
    appendFileSync(log,JSON.stringify({timer_and_methods_restored:restored,id:c.id,key:c.key,expected:c.expected,observed:obj.check.passed,msg:obj.check.msg,error:obj.error})+"\n");
}
