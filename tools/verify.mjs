// Проверка содержимого курса в том же Python, что и в браузере (Pyodide).
//   uv run tools/build.py --export build/tasks.json
//   node tools/verify.mjs build/tasks.json [фильтр-урока]
// Для каждой задачи: эталон проходит проверку, заготовка — нет.
// Для каждого примера в теории: выполняется без ошибок (или с ошибкой, если помечен `python error`).
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const [file, filter] = process.argv.slice(2);
if (!file) { console.error('usage: node tools/verify.mjs tasks.json [фильтр]'); process.exit(2); }
const items = JSON.parse(readFileSync(file, 'utf-8')).filter((x) => !filter || x.lesson.includes(filter));

const pyDir = join(root, 'site/assets/vendor/pyodide') + '/';
const { loadPyodide } = await import(pathToFileURL(pyDir + 'pyodide.mjs').href);
const py = await loadPyodide({ indexURL: pyDir });
py.FS.writeFile('/home/pyodide/_dsc_harness.py', readFileSync(join(root, 'site/assets/harness.py'), 'utf-8'));
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import _dsc_harness');
const run = py.pyimport('_dsc_harness').run;

const written = new Set();
function putFiles(files) {
  for (const f of files || []) {
    if (written.has(f)) continue;
    py.FS.writeFile('/home/pyodide/' + f, readFileSync(join(root, 'site/data', f)));
    written.add(f);
  }
}
// файлы, которые код ученика мог создать сам (например, отчёт), между задачами не должны мешать
function cleanCwd() {
  for (const name of py.FS.readdir('/home/pyodide')) {
    if (name.startsWith('.') || name === '_dsc_harness.py' || written.has(name)) continue;
    try { py.FS.unlink('/home/pyodide/' + name); } catch (e) {}
  }
}

async function exec(code, check, setup, display) {
  await py.loadPackagesFromImports(((all) => /read_excel|to_excel|ExcelFile|ExcelWriter/.test(all) ? all + '\nimport openpyxl' : all)([setup || '', code, check || ''].join('\n')), { messageCallback() {}, errorCallback() {} });
  const r = run(code, check ?? null, setup ?? null, !!display);
  const js = r.toJs({ dict_converter: Object.fromEntries });
  r.destroy();
  return js;
}

let bad = 0, n = 0;
for (const it of items) {
  n++;
  putFiles(it.files); cleanCwd();
  const tag = `${it.lesson} ${it.id}`;
  if (it.kind === 'predict') {
    // правильный вариант ответа должен совпадать с настоящим выводом кода
    const r = await exec(it.code, null, null, it.display);
    const want = it.answer.replace(/^`|`$/g, '').trim();
    if (/^Ошибка/.test(want)) {
      const type = (want.match(/[A-Z][A-Za-z]+Error/) || [])[0];
      if (r.ok || (type && r.error.type !== type)) { bad++; console.log(`✗ ${tag}: ожидалась ${want}, а получилось`, r.ok ? JSON.stringify(r.out) : r.error.type); }
    } else {
      const got = (r.out || '').trim().split('\n').map((l) => l.trim()).join(' | ');
      if (!r.ok || got !== want) { bad++; console.log(`✗ ${tag}: правильный ответ «${want}», а код выводит «${got}»`, r.error?.text || ''); }
    }
    continue;
  }
  if (it.kind === 'cell') {
    const r = await exec(it.code, null, null, it.display);
    if (it.expect_error ? r.ok : !r.ok) {
      bad++; console.log(`✗ ${tag}: пример ${it.expect_error ? 'должен падать' : 'упал'}`, r.error?.text || '');
    }
    continue;
  }
  const good = await exec(it.solution, it.check, it.setup, it.display);
  if (!good.check?.passed) {
    bad++; console.log(`✗ ${tag}: эталон не прошёл — ${good.check?.msg}`, good.error?.text || '');
  }
  cleanCwd();
  const start = await exec(it.starter, it.check, it.setup, it.display);
  if (start.check?.passed) { bad++; console.log(`✗ ${tag}: заготовка проходит проверку`); }
}
console.log(`${bad ? '✗' : '✓'} проверено: ${n}, проблем: ${bad}`);
process.exit(bad ? 1 : 0);
