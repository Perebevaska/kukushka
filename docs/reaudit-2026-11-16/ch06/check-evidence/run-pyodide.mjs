import {readFileSync,writeFileSync,appendFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=dirname(fileURLToPath(import.meta.url));const root=resolve(here,'../../../..');
const phase=process.argv[2]||'original';
const tasks=new Map(JSON.parse(readFileSync(resolve(here,`tasks-${phase}.json`))).map(t=>[t.lesson.split('/').at(-1)+'/'+t.id,t]));
const probes=JSON.parse(readFileSync(resolve(here,`probes-${phase}.json`)));
const vendor=resolve(root,'site/assets/vendor/pyodide')+'/';
const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs').href);const py=await loadPyodide({indexURL:vendor});
await py.loadPackage(['numpy','pandas','scipy','scikit-learn','matplotlib'],{messageCallback(){},errorCallback(){}});
py.FS.writeFile('/home/pyodide/_dsc_harness.py',readFileSync(resolve(here,'harness.py')));
py.runPython('import sys; sys.path.insert(0,"/home/pyodide"); import _dsc_harness');
for(const t of tasks.values())for(const f of t.files||[])py.FS.writeFile('/home/pyodide/'+f,readFileSync((existsSync(resolve(here,'data-baseline',f))?resolve(here,'data-baseline',f):resolve(root,'site/data',f))));
const run=py.pyimport('_dsc_harness').run;let file=resolve(here,`pyodide-${phase}.jsonl`);let rerun=1;while(existsSync(file)){file=resolve(here,`pyodide-${phase}-rerun${rerun++}.jsonl`);}
writeFileSync(file,JSON.stringify({kind:'environment',node:process.version,pyodide:py.version,versions:py.runPython('import numpy,pandas,sklearn; [sys.version,numpy.__version__,pandas.__version__,sklearn.__version__]').toJs()})+'\n');
function exec(code,check,setup){const r=run(code,check,setup,false);const o=r.toJs({dict_converter:Object.fromEntries});r.destroy();return o;}
for(const p of probes){const t=tasks.get(p.key);for(const f of t.files||[])py.FS.writeFile('/home/pyodide/'+f,readFileSync(p.file_variants?.[f]?resolve(here,p.file_variants[f]):(existsSync(resolve(here,'data-baseline',f))?resolve(here,'data-baseline',f):resolve(root,'site/data',f))));const setup=(t.setup||'')+'\n'+(p.setup_append||'');const r=exec(p.code,t.check,setup);const record={...p,result:r,observed:!!r.check?.passed};if(p.diagnostic)record.diagnostic_result=exec(p.code+'\nimport json as _auditjson\nprint(_auditjson.dumps('+p.diagnostic+'))',null,setup);appendFileSync(file,JSON.stringify(record)+'\n');console.log(p.id,p.key,p.expected,record.observed,r.check?.msg||r.error?.text||'');}
