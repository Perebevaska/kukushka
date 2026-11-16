import {readFileSync,writeFileSync,appendFileSync} from 'node:fs';
import {join,dirname,resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const base=dirname(fileURLToPath(import.meta.url));
const root=resolve(base,'../../../..');
const file=process.argv[2]||join(base,'original-course.json');
const out=process.argv[3]||join(base,'pyodide-original.jsonl');
const tasks=new Map(JSON.parse(readFileSync(file,'utf8')).filter(x=>x.kind==='task').map(x=>[`${x.lesson}/${x.id}`,x]));
const cases=JSON.parse(readFileSync(process.argv[5]||join(base,'cases.json'),'utf8'));
const pyDir=join(root,'site/assets/vendor/pyodide/');
const {loadPyodide}=await import(pathToFileURL(pyDir+'pyodide.mjs').href);
const py=await loadPyodide({indexURL:pyDir});
py.FS.writeFile('/home/pyodide/harness.py',readFileSync(join(root,'site/assets/harness.py'),'utf8'));
py.runPython('import sys;sys.path.insert(0,"/home/pyodide");import harness');
await py.loadPackage(['numpy','pandas','scipy','statsmodels','matplotlib'],{messageCallback(){},errorCallback(){}});
const meta=py.runPython('import json,platform,numpy,pandas,scipy,statsmodels;json.dumps(dict(runtime="Pyodide",python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,scipy=scipy.__version__,statsmodels=statsmodels.__version__))');
writeFileSync(out,meta+'\n');
const run=py.pyimport('harness').run;
for(let i=0;i<cases.length;i++){
 const c=cases[i];if(process.argv[4]&&c.name!==process.argv[4])continue;const t=tasks.get(`${c.lesson}/${c.id}`),d=`/tmp/ch05case${i}`;
 py.FS.mkdir(d);
 for(const f of t.files||[])py.FS.writeFile(d+'/'+f,readFileSync(join(root,'site/data',f)));
 py.runPython(`import os;os.chdir(${JSON.stringify(d)})`);
 const r=run(c.code,t.check,t.setup||null,false);const result=r.toJs({dict_converter:Object.fromEntries});r.destroy();
 const actual=!!(result.ok&&result.check?.passed);
 appendFileSync(out,JSON.stringify({...c,actual,matches:actual===c.expected,result})+'\n');
 console.log(c.lesson,c.id,c.name,c.expected,actual);
}
