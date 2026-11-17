import fs from 'node:fs';import path from 'node:path';import {pathToFileURL,fileURLToPath} from 'node:url';import crypto from 'node:crypto';
const base=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(base,'../../../../../..');
const phase=process.argv[2]||'before',mode=process.argv[3]||'smokes';
const input=JSON.parse(fs.readFileSync(base+'/syntax-inputs.json','utf8'));
const vendor=root+'/site/assets/vendor/pyodide/';const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs'));
const py=await loadPyodide({indexURL:vendor});
const harnessFile=phase==='before'?base+'/../frozen_harness.py':root+'/site/assets/harness.py';
py.FS.writeFile('/home/pyodide/controlled_harness.py',fs.readFileSync(harnessFile));py.runPython('import sys;sys.path.insert(0,"/home/pyodide");import controlled_harness');const run=py.pyimport('controlled_harness').run;
const records=[];
async function one(name,probe,showLast=false){
 const folder='/tmp/'+name;try{py.FS.mkdir(folder)}catch{};py.FS.chdir(folder);
 for(const file of probe.files||[])py.FS.writeFile(folder+'/'+file,fs.readFileSync(base+'/data/'+file));
 const imports=[];try{await py.loadPackagesFromImports([probe.setup||'',probe.code,probe.check||''].join('\n'),{messageCallback:m=>imports.push(String(m)),errorCallback:e=>imports.push(String(e))});}catch(e){imports.push('loader:'+String(e));}
 const result=run(probe.code,probe.check??null,probe.setup||'',showLast);const raw=result.toJs({dict_converter:Object.fromEntries});result.destroy();records.push({name,imports,raw});
}
if(mode==='smokes'){
 for(const probe of input.valid_smokes)await one(probe.name,probe,probe.show_last);
}else{
 const bad=input.cold_warm_cases.find(r=>r.name==='literal_invalid'),good=input.cold_warm_cases.find(r=>r.name==='literal_fixed');
 if(mode==='cold-bad')await one('cold_invalid',bad);
 else if(mode==='warm-sequence'){await one('cold_fixed',good);await one('warm_invalid_after_fixed',bad);await one('warm_fixed',good);}
 else throw Error('Unknown matrix mode');
}
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
fs.writeFileSync(base+'/'+phase+'-syntax-'+mode+'.json',JSON.stringify({phase,mode,node:process.version,pyodide:py.version,harness_sha256:sha(harnessFile),input_sha256:sha(base+'/syntax-inputs.json'),records},null,2));console.log(phase,mode,records.map(r=>[r.name,r.raw.ok,r.raw.error?.type,r.raw.error?.line,r.raw.check?.passed]));
