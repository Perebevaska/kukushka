import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [phase, exportPath] = process.argv.slice(2);
const here = path.dirname(fileURLToPath(import.meta.url));
const chapter = path.resolve(here, '../..');
const root = path.resolve(chapter, '../../..');
const vendor = path.resolve(root, 'site/assets/vendor/pyodide') + '/';
const {loadPyodide} = await import(pathToFileURL(vendor+'pyodide.mjs'));
const py = await loadPyodide({indexURL: vendor});
py.FS.writeFile('/home/pyodide/course_harness.py', fs.readFileSync(path.join(root,'site/assets/harness.py')));
py.runPython('import sys, os; sys.path.insert(0, "/home/pyodide"); import course_harness');
const grade = py.pyimport('course_harness').run;
const rows = fs.readFileSync(path.join(here, 'programs.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
const loaded = JSON.parse(fs.readFileSync(exportPath, 'utf8')).filter(t => t.kind === 'task');
const tasks = new Map(loaded.map(t => [t.lesson+'/'+t.id, t]));
const dest = path.join(here, phase+'-pyodide.jsonl');
fs.writeFileSync(dest, '');
for (const row of rows) {
    const t = tasks.get(row.lesson+'/'+row.task);
    const folder = '/tmp/'+row.id;
    py.FS.mkdir(folder);
    py.runPython('os.chdir("'+folder+'")');
    for (const f of t.files) py.FS.writeFile(folder+'/'+f, fs.readFileSync(path.join(chapter,'technical/data-baseline',f)));
    await py.loadPackagesFromImports([t.setup,row.code,t.check].join('\n'), {messageCallback(){},errorCallback(){}});
    const raw = grade(row.code,t.check,t.setup||'',false);
    const r = raw.toJs({dict_converter:Object.fromEntries});
    raw.destroy();
    fs.appendFileSync(dest, JSON.stringify({id:row.id,ok:r.ok,passed:r.check.passed,msg:r.check.msg,error:r.error,stdout:r.out})+'\n');
}
grade.destroy();
