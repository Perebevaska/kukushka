import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

// From repository root: node path/to/expert-run.mjs /path/to/export.json > /path/to/output.json
const vendor = resolve('site/assets/vendor/pyodide') + '/';
const { loadPyodide } = await import(pathToFileURL(vendor + 'pyodide.mjs'));
const py = await loadPyodide({indexURL: vendor, stdout() {}, stderr() {}});
const items = JSON.parse(readFileSync(process.argv[2])).filter(row => row.lesson.startsWith('ch05/'));
await py.loadPackage(['numpy','pandas','scipy','statsmodels','matplotlib'], {messageCallback() {}, errorCallback() {}});
for (const f of new Set(items.flatMap(row => row.files || [])))
  py.FS.writeFile(f,readFileSync(resolve('site/data',f)));
py.FS.writeFile('_dsc_harness.py',readFileSync('site/assets/harness.py'));
py.runPython('import sys; sys.path.insert(0, ".")');
const evidence = JSON.parse(py.runPython(readFileSync(new URL('expert-data.py',import.meta.url),'utf8')));
const run = py.pyimport('_dsc_harness').run;
const examples=[];
for (const item of items.filter(row=>['cell','predict'].includes(row.kind))) {
  const result=run(item.code,null,null,!!item.display);
  const {ok,out,error}=result.toJs({dict_converter:Object.fromEntries});
  result.destroy();
  examples.push({lesson:item.lesson,id:item.id,ok,out,error:error?.type || null});
}
console.log(JSON.stringify({pyodide:py.version,...evidence,examples},null,2));
