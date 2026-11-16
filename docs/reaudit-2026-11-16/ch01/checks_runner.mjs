// Limited independent checks. Does not run verify.mjs or historical programs.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const folder = path.resolve('docs/reaudit-2026-11-16/ch01');
const tasks = new Map(JSON.parse(fs.readFileSync(folder + '/checks_tasks.json', 'utf8'))
  .map(item => [item.lesson + '/' + item.id, item]));
const programs = fs.readFileSync(folder + '/checks_programs.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
const vendor = path.resolve('site/assets/vendor/pyodide') + '/';
const {loadPyodide} = await import(pathToFileURL(vendor + 'pyodide.mjs'));
const py = await loadPyodide({indexURL: vendor});
py.FS.writeFile('/home/pyodide/check_harness.py', fs.readFileSync('site/assets/harness.py'));
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import check_harness');
const grade = py.pyimport('check_harness').run;
const results = [];
for (const [index, program] of programs.entries()) {
  const item = tasks.get(program.lesson + '/' + program.task);
  const cwd = '/tmp/check-' + index;
  py.FS.mkdir(cwd);
  py.runPython('import os; os.chdir(' + JSON.stringify(cwd) + ')');
  for (const file of item.files) py.FS.writeFile(cwd + '/' + file, fs.readFileSync('site/data/' + file));
  for (const [file, text] of Object.entries(program.files_override || {})) py.FS.writeFile(cwd + '/' + file, text);
  const result = grade(program.code, program.check_override || item.check, item.setup || '', Boolean(item.display));
  const js = result.toJs({dict_converter: Object.fromEntries});
  result.destroy();
  let reportMd = null;
  try { reportMd = py.FS.readFile(cwd + '/report.md', {encoding: 'utf8'}); } catch {}
  const record = {...program, runtime: py.runPython('sys.version'), pyodide: py.version, result: js, report_md: reportMd};
  results.push(record);
  console.log(JSON.stringify({id: program.id, expected: program.expected, ...js}));
}
fs.writeFileSync(folder + '/checks_pyodide.jsonl', results.map(row => JSON.stringify(row)).join('\n') + '\n');
grade.destroy();
