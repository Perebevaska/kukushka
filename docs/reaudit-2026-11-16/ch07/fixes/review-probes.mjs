/* node review-probes.mjs before|after html|notebook [own|all]  (from repository root) */
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url)), chapter=path.dirname(here);
const [phase,source,subset='all']=process.argv.slice(2);
const sha=x=>createHash('sha256').update(x).digest('hex');
const read=f=>phase==='before'?execFileSync('git',['show','6a82748:'+f],{maxBuffer:32e6}):fs.readFileSync(f);
const hashes={}, tasks=new Map();
const open=f=>{const bytes=read(f);hashes[f]=sha(bytes);return bytes;};
if(source==='html'){
 for(const file of fs.readdirSync('site/ch07').filter(n=>n.endsWith('.html'))){
  const html=open('site/ch07/'+file).toString();const m=html.match(/<script type="application\/json" id="lesson-data">([\s\S]*?)<\/script>/);if(!m)continue;
  const d=JSON.parse(m[1]);for(const t of d.tasks) tasks.set(d.lesson.split('/').at(-1)+'/'+t.id,{...t,files:d.files});
 }
}else{
 const cat=JSON.parse(open('site/notebooks/tasks/ch07.json')).tasks;
 for(const [k,t] of Object.entries(cat))tasks.set(k.slice(5),t);
}
const artifactTasks=tasks.size;
const audited=JSON.parse(fs.readFileSync(chapter+'/check-evidence/tasks-reviewed.json'));
for(const t of audited.filter(x=>x.lesson.endsWith('/contracts')))tasks.set('contracts/'+t.id,t);
let probes=JSON.parse(fs.readFileSync(chapter+'/check-evidence/probes-reviewed.json'));
const own=JSON.parse(fs.readFileSync(here+'/review-own.json'));
for(const a of own){
 const t=tasks.get(a.key);
 let code=a.base==='solution'?[t.starter,t.solution].join('\n'):probes.find(x=>x.id===a.base).code;
 if(a.replace){if(!code.includes(a.replace[0])) throw Error('Нет фрагмента '+a.id);code=code.replace(a.replace[0],a.replace[1]);}
 probes.push({...a,code:code+'\n'+(a.append||'')});
}
if(subset==='legacy'){
 probes=['original','original-extra','ties-original','pipe-original','display-before'].flatMap(group=>JSON.parse(fs.readFileSync(chapter+'/check-evidence/probes-'+group+'.json')).map(p=>({...p,id:group+'/'+p.id})));
 const attempts=fs.readFileSync(chapter+'/student/09-attempt1.jsonl','utf8').trim().split('\n').map(JSON.parse);
 for(const t of attempts.filter(t=>['look','pipe'].includes(t.task)))probes.push({key:'09-project/'+t.task,id:'student-original/'+t.task,code:t.code,expected:true});
}
if(subset==='own')probes=probes.filter(p=>own.some(x=>x.id===p.id));
const vendor=path.resolve('site/assets/vendor/pyodide')+'/';
const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs'));
const py=await loadPyodide({indexURL:vendor});await py.loadPackage(['scikit-learn','pandas','matplotlib','joblib'],{messageCallback(){},errorCallback(){}});
py.FS.writeFile('review_harness.py',open('site/assets/harness.py'));
py.runPython('import sys, os;sys.path.insert(0,os.getcwd());import review_harness');
const run=py.pyimport('review_harness').run;
const dest=here+'/review-'+phase+'-'+source+(subset==='all'?'':'-'+subset)+'.jsonl';
fs.writeFileSync(dest,JSON.stringify({phase,source,published_tasks:artifactTasks,node:process.version,pyodide:py.version,hashes})+'\n');
for(const p of probes){
 const t=tasks.get(p.key);if(!t)throw Error(p.key);
 for(const f of t.files||[])py.FS.writeFile(f,fs.readFileSync(chapter+'/technical/data-baseline/'+f));
 if(py.FS.analyzePath('churn_model.joblib').exists)py.FS.unlink('churn_model.joblib');
 if(p.csv_transform)py.runPython(p.csv_transform);
 const r=run(p.code,t.check,(t.setup||'')+'\n'+(p.setup_append||''),false);const v=r.toJs({dict_converter:Object.fromEntries});r.destroy();
 const row={id:p.id,key:p.key,expected:p.expected,passed:!!v.check?.passed,message:v.check?.msg||v.error?.text||null,output:v.stdout||v.out||null,sha256_code:sha(p.code)};
 fs.appendFileSync(dest,JSON.stringify(row)+'\n');if(row.passed!==row.expected)console.log(row.id,row.passed,row.message);
}
