import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const dir = dirname(fileURLToPath(import.meta.url));
const checks = resolve(dir, '../checks');
const root = resolve(dir, '../../../../..');
const vendor = join(root, 'site/assets/vendor/pyodide');
const [phase = 'before', tasksPath = join(checks, 'tasks.json')] = process.argv.slice(2);
const contents = readFileSync(join(dir, 'programs.jsonl'), 'utf8');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const freeze = JSON.parse(readFileSync(join(dir, 'freeze.json')));
if (digest(contents) !== freeze.programs_sha256) throw Error('Frozen programs changed');
const programs = contents.trim().split('\n').map(JSON.parse);
const taskBytes = readFileSync(tasksPath);
const tasks = JSON.parse(taskBytes);
const { loadPyodide } = await import(pathToFileURL(join(vendor, 'pyodide.mjs')));
const py = await loadPyodide({indexURL: vendor + '/'});
await py.loadPackage(['pandas','numpy','scikit-learn','matplotlib'], {messageCallback() {}});
py.runPython(readFileSync(join(checks, 'frozen_harness.py'), 'utf8'));
const run = py.globals.get('run');
const entries = [];
for (const row of programs) {
    const task = tasks.find(t => row.lesson === t.lesson && row.task === t.id);
    for (const name of task.files) {
        py.FS.writeFile(name, readFileSync(join(checks,'data',name)));
    }
    const output = run(row.code, task.check, task.setup, !!task.display);
    const result = output.toJs({dict_converter:Object.fromEntries});
    output.destroy();
    entries.push({name: row.name, expected: row.expected, passed: result.check.passed,
        ok: result.ok, message: result.check.msg, error: result.error,
        figureCount: result.figs.length, code_sha256: row.sha256});
    console.log(row.name, row.expected, result.check.passed, result.error?.type ?? '');
}
writeFileSync(join(dir, phase + '-pyodide.json'), JSON.stringify({
    runtime:py.version, executed_utc: new Date().toISOString(), task_sha256:digest(taskBytes),
    programs_sha256:freeze.programs_sha256, entries
}, null, 2));
