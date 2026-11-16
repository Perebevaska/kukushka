import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
const [phase,exportFile,harness,dataDir,casesFile,vendor] = process.argv.slice(2);
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const tasks=JSON.parse(fs.readFileSync(exportFile)).filter(t=>t.lesson.startsWith('ch13/') && t.kind==='task');
const cases=JSON.parse(fs.readFileSync(casesFile));
const {loadPyodide}=await import(pathToFileURL(path.join(vendor,'pyodide.mjs')).href);
const py=await loadPyodide({indexURL:path.resolve(vendor)+'/'});
await py.loadPackage(['pandas','numpy','scipy','scikit-learn','matplotlib'],{messageCallback(){},errorCallback(){}});
py.FS.writeFile('review_harness.py',fs.readFileSync(harness));
py.runPython('import review_harness');
const run=py.pyimport('review_harness').run;
for(const name of fs.readdirSync(dataDir).filter(n=>n.endsWith('.csv'))) py.FS.writeFile(name,fs.readFileSync(path.join(dataDir,name)));
const meta={pyodide:py.version,python:py.runPython('import sys;sys.version'),packages:py.runPython('import pandas,numpy,scipy,sklearn,matplotlib; [m.__version__ for m in (pandas,numpy,scipy,sklearn,matplotlib)]').toJs(),wasm:sha(path.join(vendor,'pyodide.asm.wasm')),harness:sha(harness),cases:sha(casesFile),export:sha(exportFile)};
fs.writeFileSync(path.join(dir,phase+'-pyodide-meta.json'),JSON.stringify(meta,null,2)+'\n');
const output=path.join(dir,phase+'-pyodide.jsonl');
fs.writeFileSync(output,'');
for(const {id,task,code,expected} of cases){
  const t=tasks.find(x=>x.id===task);
  const raw=run(code,t.check,t.setup,!!t.display);
  const r=raw.toJs({dict_converter:Object.fromEntries});raw.destroy();
  fs.appendFileSync(output,JSON.stringify({id,task,expected,ok:r.ok,check:r.check,error:r.error,out:r.out,figures:r.figs.length})+'\n');
  console.log(id,r.check.passed);
}
