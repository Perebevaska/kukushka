import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const phase=process.argv[2];
if (!['before','after'].includes(phase)) throw Error('before or after required');
const bundle=process.argv[3]||phase;
const here=path.dirname(new URL(import.meta.url).pathname);
const root=path.resolve(here,'../../../..');
const items=JSON.parse(fs.readFileSync(path.join(here,phase+'-tasks.json'),'utf8'));
const tasks=new Map(items.map(t=>[t.lesson+'/'+t.id,t]));
const rows=fs.readFileSync(path.join(here,process.argv[3]?(bundle+'-programs.jsonl'):(phase==='after'?'after-programs.jsonl':'programs.jsonl')),'utf8').trim().split('\n').map(JSON.parse);
const vendor=path.join(root,'site/assets/vendor/pyodide/');
const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs'));
const py=await loadPyodide({indexURL:vendor});
py.FS.writeFile('/home/pyodide/course_harness.py',fs.readFileSync(path.join(root,'site/assets/harness.py')));
py.runPython('import sys; sys.path.insert(0,"/home/pyodide"); import course_harness');
const grade=py.pyimport('course_harness').run;
const results=[];
for (const [index,row] of rows.entries()) {
 const item=tasks.get(row.lesson+'/'+row.task);
 const folder='/tmp/checks-'+phase+'-'+index; py.FS.mkdir(folder);
 py.runPython('import os; os.chdir('+JSON.stringify(folder)+')');
 const copy=()=>{for(const name of item.files) py.FS.writeFile(folder+'/'+name,fs.readFileSync(path.join(here,'data-baseline',name)));};
 copy();
 await py.loadPackagesFromImports([item.setup,row.code,item.check].join('\n'),{messageCallback(){},errorCallback(){}});
 let setup=item.setup||'';
 if(row.clock_ticks) setup+='\n_fixture_ticks=iter('+JSON.stringify(row.clock_ticks)+')\n_measurement_clock=lambda:next(_fixture_ticks)\n';
 const raw=grade(row.code,item.check,setup,false); const r=raw.toJs({dict_converter:Object.fromEntries}); raw.destroy();
 const result={...row,ok:r.ok,passed:r.check.passed,message:r.check.msg,error:r.error,stdout:r.out};
 if(row.oracle){copy();const raw2=grade(row.code,item.check+'\n'+row.oracle,item.setup||'',false);const o=raw2.toJs({dict_converter:Object.fromEntries});raw2.destroy();result.transfer_oracle={ok:o.ok,check:o.check,error:o.error};}
 result.failure_stage=!r.ok?'execution':r.check.msg.startsWith('Проверка споткнулась:')?'check-exception':!r.check.passed?'check-assertion':null;
 result.execution_error_type=r.error?.type||null;
 results.push(result);
 fs.writeFileSync(path.join(here,bundle+'-pyodide.jsonl'),results.map(r=>JSON.stringify(r)).join('\n')+'\n');
 console.log(JSON.stringify(Object.fromEntries(['id','lesson','task','expected','ok','passed','message'].map(k=>[k,result[k]]))));
}
await py.loadPackagesFromImports('import numpy,pandas,scipy,sklearn',{messageCallback(){},errorCallback(){}});
fs.writeFileSync(path.join(here,bundle+'-pyodide-environment.json'),JSON.stringify({node:process.version,pyodide:py.version,versions:py.runPython('import sys,numpy,pandas,scipy,sklearn; [sys.version,numpy.__version__,pandas.__version__,scipy.__version__,sklearn.__version__]').toJs()},null,2));
grade.destroy();console.log('Completed',results.length,'programs; normative matches',results.filter(r=>r.passed===r.expected).length);
