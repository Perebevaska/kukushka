import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [ch,lesson] = process.argv.slice(2), root=process.cwd(), work='/tmp/ku-audit/'+ch;
const data=JSON.parse(fs.readFileSync('/tmp/ku-audit/tasks.json','utf8')).filter(x=>x.kind==='task' && x.lesson.startsWith(ch+'/'));
const pyDir=root+'/site/assets/vendor/pyodide/';
const {loadPyodide}=await import(pathToFileURL(pyDir+'pyodide.mjs').href);
const py=await loadPyodide({indexURL:pyDir});
py.FS.writeFile('/home/pyodide/_dsc_harness.py',fs.readFileSync('site/assets/harness.py','utf8'));
py.runPython('import sys; sys.path.insert(0,"/home/pyodide"); import _dsc_harness');
const run=py.pyimport('_dsc_harness').run;
const log=work+'/checks.jsonl';
const seen=fs.existsSync(log)?fs.readFileSync(log,'utf8').trim().split('\n').filter(Boolean).map(JSON.parse):[];
const rows=fs.readFileSync(work+'/submissions.jsonl','utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
for(const [i,row] of rows.entries()){
  if(lesson && row.lesson!==lesson)continue;
  if(seen.some(x=>x.row===i && x.code===row.code))continue;
  const item=data.find(x=>x.lesson===ch+'/'+row.lesson && x.id===row.id);
  if(!item){console.log(row.lesson,row.id,'UNKNOWN');continue;}
  for(const f of item.files||[])py.FS.writeFile('/home/pyodide/'+f,fs.readFileSync('site/data/'+f));
  const src=[item.setup,row.code,item.check].join('\n');
  await py.loadPackagesFromImports(src+(/read_excel|to_excel|ExcelFile|ExcelWriter/.test(src)?'\nimport openpyxl':''),{messageCallback(){},errorCallback(){}});
  const ob=run(row.code,item.check,item.setup||'',!!item.display);
  const r=ob.toJs({dict_converter:Object.fromEntries});ob.destroy();
  const passed=!!r.check?.passed,msg=r.error?.text||r.check?.msg||'';
  fs.appendFileSync(log,JSON.stringify({row:i,lesson:row.lesson,id:row.id,code:row.code,passed,msg})+'\n');
  console.log(row.id,passed?'ok':msg.slice(0,600));
}
