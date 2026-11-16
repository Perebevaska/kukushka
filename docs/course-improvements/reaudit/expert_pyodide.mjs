// node expert_pyodide.mjs /path/to/tasks.json /path/to/exported-expert-programs.jsonl
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const [exportFile, submissionsFile] = process.argv.slice(2);
const tasks = new Map(JSON.parse(fs.readFileSync(exportFile, 'utf8'))
  .filter(item => item.kind === 'task').map(item => [item.lesson + '/' + item.id, item]));
const programs = fs.readFileSync(submissionsFile, 'utf8').trim().split('\n').map(JSON.parse);
const vendor = path.resolve('site/assets/vendor/pyodide') + '/';
const {loadPyodide} = await import(pathToFileURL(vendor + 'pyodide.mjs'));
const py = await loadPyodide({indexURL: vendor});
py.FS.writeFile('/home/pyodide/course_harness.py', fs.readFileSync('site/assets/harness.py'));
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import course_harness');
const grade = py.pyimport('course_harness').run;
for (const [index, {lesson, task, code, expected, description}] of programs.entries()) {
  const item = tasks.get(lesson + '/' + task);
  const directory = '/tmp/expert-' + index;
  py.FS.mkdir(directory);
  py.runPython('import os; os.chdir(' + JSON.stringify(directory) + ')');
  for (const file of item.files) py.FS.writeFile(directory + '/' + file, fs.readFileSync('site/data/' + file));
  let imports = [item.setup, code, item.check].join('\n');
  if (/read_excel|to_excel|ExcelFile|ExcelWriter/.test(imports)) imports += '\nimport openpyxl';
  await py.loadPackagesFromImports(imports, {messageCallback() {}, errorCallback() {}});
  const result = grade(code, item.check, item.setup || '', Boolean(item.display));
  const {ok, check, out, error} = result.toJs({dict_converter: Object.fromEntries});
  result.destroy();
  console.log(JSON.stringify({lesson, task, expected, description, ok, passed: check.passed,
                             message: check.msg, stdout: out, error}));
}
grade.destroy();
