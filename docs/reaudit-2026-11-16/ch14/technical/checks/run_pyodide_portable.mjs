import fs from 'node:fs';import path from 'node:path';import {pathToFileURL,fileURLToPath} from 'node:url';import crypto from 'node:crypto';
const base=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(base,'../../../../..'),phase=process.argv[2]||'before',taskFile=process.argv[3]||base+'/tasks.json';
const rows=fs.readFileSync(base+'/programs.jsonl','utf8').trim().split('\n').map(JSON.parse),tasks=JSON.parse(fs.readFileSync(taskFile));
const vendor=root+'/site/assets/vendor/pyodide/';const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs'));const py=await loadPyodide({indexURL:vendor});
await py.loadPackage(['numpy','pandas','scipy','scikit-learn','matplotlib','pillow'],{messageCallback(){},errorCallback(){}});
py.FS.writeFile('/home/pyodide/frozen_harness.py',fs.readFileSync(base+'/frozen_harness.py'));py.runPython('import sys;sys.path.insert(0,"/home/pyodide");import frozen_harness');const run=py.pyimport('frozen_harness').run;
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const meta={node:process.version,pyodide:py.version,python:py.runPython('sys.version'),libraries:py.runPython('import numpy,pandas,scipy,sklearn,matplotlib;[numpy.__version__,pandas.__version__,scipy.__version__,sklearn.__version__,matplotlib.__version__]').toJs(),task_sha256:sha(taskFile),programs_sha256:sha(base+'/programs.jsonl'),harness_sha256:sha(base+'/frozen_harness.py'),runtime_files:Object.fromEntries(['pyodide.mjs','pyodide.asm.wasm','python_stdlib.zip','pyodide-lock.json'].map(f=>[f,sha(vendor+f)]))};fs.writeFileSync(base+'/'+phase+'-pyodide-meta.json',JSON.stringify(meta,null,2));
const output=base+'/'+phase+'-pyodide.jsonl';const seen=new Set(fs.existsSync(output)?fs.readFileSync(output,'utf8').trim().split('\n').filter(Boolean).map(s=>JSON.parse(s).index):[]);
for(const [index,row] of rows.entries()){
 if(seen.has(index))continue;
 const t=tasks.find(t=>t.lesson===row.lesson&&t.id===row.task);for(const f of t.files)py.FS.writeFile('/home/pyodide/'+f,fs.readFileSync(base+'/data/'+f));
 let raw;const start=Date.now();try{const ob=run(row.code,t.check,t.setup,!!t.display);raw=ob.toJs({dict_converter:Object.fromEntries});ob.destroy();}catch(e){raw={transport_error:String(e)}}
 const stage=raw.transport_error?'transport':!raw.ok?'submission_execution':!raw.check?.passed?'check':'accepted';const passed=!!raw.check?.passed;
 fs.appendFileSync(output,JSON.stringify({...row,index,phase,runtime:'Pyodide shipped vendor',duration_s:(Date.now()-start)/1000,stage,passed,raw})+'\n');console.log(index,row.task,row.label,passed,row.expected,stage);
}
