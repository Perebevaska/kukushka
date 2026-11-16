import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const root=process.cwd();
const D=root+'/docs/reaudit-2026-11-16/ch02/check-evidence';
const pyDir=root+'/site/assets/vendor/pyodide/';
const {loadPyodide}=await import(pathToFileURL(pyDir+'pyodide.mjs').href);
const py=await loadPyodide({indexURL:pyDir});
py.FS.writeFile('/home/pyodide/_dsc_harness.py',readFileSync(root+'/site/assets/harness.py','utf8'));
py.runPython('import sys;sys.path.insert(0,"/home/pyodide");import _dsc_harness');
const run=py.pyimport('_dsc_harness').run;
await py.loadPackage(['pandas','matplotlib','duckdb']);
const reviewBefore=process.argv.includes('--review-before');
const promoBefore=process.argv.includes('--promo-before');
const roundingBefore=process.argv.includes('--promo-rounding-before');
const after=process.argv.includes('--after')||reviewBefore||promoBefore||roundingBefore;
const taskMap=after?new Map(JSON.parse(readFileSync(D+(roundingBefore?'/tasks-before-promo-rounding-fix.json':promoBefore?'/tasks-before-promo-fix.json':reviewBefore?'/tasks-before-review-fixes.json':'/tasks-after.json'),'utf8')).filter(x=>x.kind==='task').map(x=>[x.lesson.split('/').at(-1)+'/'+x.id,x])):null;
const cases=JSON.parse(readFileSync(D+'/probes-before.json','utf8')),results=[];
console.log(py.runPython('import sys,pandas;sys.version+" pandas "+pandas.__version__'));
if(after){for(const x of cases){const t=taskMap.get(x.lesson+'/'+x.task);x.check=t.check;x.setup=t.setup;}for(const key of new Set(cases.map(x=>x.lesson+'/'+x.task))){const t=taskMap.get(key);cases.push({lesson:t.lesson.split('/').at(-1),task:t.id,case:'current-author-solution',expected:true,code:t.solution,check:t.check,setup:t.setup,files:t.files});}}
for(const x of cases){
 for(const f of x.files)py.FS.writeFile('/home/pyodide/'+f,readFileSync(root+'/site/data/'+f));
 if(x.prepare)py.runPython(x.prepare);
 const r=run(x.code,x.check,x.setup??null,false),js=r.toJs({dict_converter:Object.fromEntries});r.destroy();
 const actual=!!js.check?.passed;results.push({...x,result:js,actual,match:actual===x.expected});
 console.log((actual===x.expected?'OK ':'DEFECT ')+x.lesson+'/'+x.task+' '+x.case+' expected='+x.expected+' actual='+actual+' '+(js.check?.msg??js.error?.text??''));
}
writeFileSync(D+(roundingBefore?'/results-before-promo-rounding-fix.json':promoBefore?'/results-before-promo-fix.json':reviewBefore?'/results-before-review-fixes.json':after?'/results-after.json':'/results-before.json'),JSON.stringify(results,null,2));

if(after && !reviewBefore && !promoBefore && !roundingBefore && results.some(x=>!x.match)) process.exitCode=1;
