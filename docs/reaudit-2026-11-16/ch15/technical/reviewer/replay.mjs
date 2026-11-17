import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {createHash} from 'node:crypto';

const dir=path.dirname(fileURLToPath(import.meta.url)), technical=path.dirname(dir);
const root=path.resolve(dir,'../../../../..'), pyDir=path.join(root,'site/assets/vendor/pyodide/');
const { loadPyodide } = await import(pathToFileURL(pyDir+'pyodide.mjs').href);
const cases=JSON.parse(fs.readFileSync(path.join(dir,'frozen.json')));
cases.push(...JSON.parse(fs.readFileSync(path.join(dir,'supplement.json'))));
const baseline=path.join(technical,'baseline-export.json');
const source=process.argv[3]||baseline, phase=process.argv[2]||'before';
const index=p=>Object.fromEntries(JSON.parse(fs.readFileSync(p)).filter(x=>x.kind==='task').map(x=>[x.id,x]));
const old=index(baseline), current=index(source);
async function boot(){
  const py=await loadPyodide({indexURL:pyDir});
  py.FS.writeFile('/home/pyodide/_h.py',fs.readFileSync(path.join(root,'site/assets/harness.py')));
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide'); import _h");
  return py;
}
const out=[];
async function run(py,c,label){
  const task=current[c.task],check=c.check===old[c.task].check?task.check:c.check;
  const wd='/home/pyodide/'+label;
  py.FS.mkdir(wd);py.FS.chdir(wd);
  for(const fname of c.files)py.FS.writeFile(fname,fs.readFileSync(path.join(technical,'data-baseline',fname)));
  try {
    await py.loadPackagesFromImports([task.setup,c.code,check].join('\n'),{messageCallback(){},errorCallback(){}});
  } catch (e) {
    out.push({name:label,expected:c.should_pass,checked:null,error:String(e),stage:'loadPackagesFromImports'});
    console.log(label, 'import scan', String(e));return;
  }
  const obj=py.pyimport('_h').run(c.code,check,task.setup,false);
  const res=obj.toJs({dict_converter:Object.fromEntries});obj.destroy();
  out.push({name:label,expected:c.should_pass,checked:res.check,error:res.error,output:res.out.slice(-1000)});
  console.log(label,JSON.stringify(res.check));
}
let py=await boot();
await run(py,cases[0],'cold_literal_invalid');
py=await boot();
await run(py,cases[1],'cold_literal_fixed');
await run(py,cases[0],'warm_literal_invalid');
for(const c of cases.slice(2))await run(py,c,c.name);
fs.writeFileSync(path.join(dir,phase+'-pyodide.json'),JSON.stringify({version:py.version,export_sha:createHash('sha256').update(fs.readFileSync(source)).digest('hex'),results:out},null,2)+'\n');
