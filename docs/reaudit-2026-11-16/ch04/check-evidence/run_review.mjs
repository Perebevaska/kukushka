import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const root=process.cwd(),D=root+'/docs/reaudit-2026-11-16/ch04/check-evidence';
const taskFile=process.argv[3]||'tasks-review.json';
const tasks=new Map(JSON.parse(readFileSync(D+'/'+taskFile,'utf8')).filter(x=>x.kind==='task').map(x=>[x.lesson.split('/').at(-1)+'/'+x.id,x]));
const stem=process.argv[2]||'review';
const cases=JSON.parse(readFileSync(D+'/'+stem+'-programs.json','utf8'));
const pyDir=root+'/site/assets/vendor/pyodide/';
const {loadPyodide}=await import(pathToFileURL(pyDir+'pyodide.mjs'));
const py=await loadPyodide({indexURL:pyDir});await py.loadPackage(['pandas','matplotlib','scipy']);
py.FS.writeFile('/home/pyodide/_dsc_harness.py',readFileSync(root+'/site/assets/harness.py','utf8'));
py.runPython('import sys;sys.path.insert(0,"/home/pyodide");import _dsc_harness');
const run=py.pyimport('_dsc_harness').run,results=[];
for(const p of cases){
 const task=tasks.get(p.lesson+'/'+p.task);
 for(const f of task.files)py.FS.writeFile('/home/pyodide/'+f,readFileSync(root+'/site/data/'+f));
 if(p.prepare)py.runPython(p.prepare);
 const r=run(p.code,task.check,task.setup||null,false),result=r.toJs({dict_converter:Object.fromEntries});r.destroy();
 const actual=!!result.check?.passed,match=actual===p.expected;results.push({...p,check:task.check,setup:task.setup,files:task.files,task_snapshot:taskFile,result,actual,match});
 console.log(match?'OK':'DEFECT',p.lesson+'/'+p.task,p.case,result.check?.msg??result.error?.text??'');
}
writeFileSync(D+'/'+stem+(taskFile==='tasks-review.json'?'':'-'+taskFile.replace(/\.json$/,''))+'-pyodide.json',JSON.stringify(results,null,2));
console.log('Final',results.filter(x=>x.match).length,'of',results.length);
if(results.some(x=>!x.match))process.exitCode=1;
