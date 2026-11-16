// node docs/course-improvements/reaudit/replay.mjs /path/to/tasks.json /path/to/results.jsonl
// Run from the project root. Preserve one last, historically accepted submission per task.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';

const [exportPath, outputPath] = process.argv.slice(2);
if (!exportPath || !outputPath) throw new Error('Expected task export and output JSONL paths.');
const tasks = JSON.parse(fs.readFileSync(exportPath, 'utf8')).filter(row => row.kind === 'task');
const chapters = [...new Set(tasks.map(t => t.lesson.split('/')[0]))].sort();
const vendor = path.resolve('site/assets/vendor/pyodide') + '/';
const {loadPyodide} = await import(pathToFileURL(vendor + 'pyodide.mjs'));
fs.writeFileSync(outputPath, '');
for (const ch of chapters) {
    const source = 'docs/audit-2026-11-13/' + ch + '/' + (ch === 'ch01' ? 'browser' : 'student') + '.jsonl';
    const historical = new Map();
    fs.readFileSync(source, 'utf8').trim().split('\n').forEach((line, index) => {
        const row = JSON.parse(line);
        if (row.code && (row.browser_passed === true || row.passed === true || row.runtime_passed === true)) {
            historical.set(row.lesson + '/' + row.id, {code:row.code, line:index+1});
        }
    });
    const py = await loadPyodide({indexURL:vendor});
    py.FS.writeFile('/home/pyodide/_dsc_harness.py', fs.readFileSync('site/assets/harness.py'));
    py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import _dsc_harness');
    const run = py.pyimport('_dsc_harness').run;
    for (const task of tasks.filter(x => x.lesson.startsWith(ch+'/'))) {
        const key = task.lesson.slice(5) + '/' + task.id;
        const attempt = historical.get(key);
        const record = {chapter: ch, lesson: task.lesson.slice(5), id: task.id};
        if (!attempt) {
            record.state = 'no_historical_code';
        } else {
            record.source = source;
            record.line = attempt.line;
            record.sha256 = crypto.createHash('sha256').update(attempt.code).digest('hex');
            // A new writable directory per attempt prevents files from a previous solution earning a pass.
            const wd = '/tmp/learner-'+historical.size+'-'+attempt.line;
            py.FS.mkdir(wd);
            py.runPython('import os; os.chdir('+JSON.stringify(wd)+')');
            for (const name of task.files || []) py.FS.writeFile(wd+'/'+name, fs.readFileSync('site/data/'+name));
            const program = [task.setup, attempt.code, task.check].join('\n');
            await py.loadPackagesFromImports(program+(/read_excel|to_excel|ExcelFile|ExcelWriter/.test(program)?'\nimport openpyxl':''), {messageCallback(){}, errorCallback(){}});
            const proxy = run(attempt.code,task.check,task.setup||'',!!task.display);
            const result = proxy.toJs({dict_converter:Object.fromEntries});
            proxy.destroy();
            record.state = result.check?.passed ? 'accepted' : 'rejected';
            if (record.state === 'rejected') record.feedback = [result.error?.text,result.check?.msg].filter(Boolean).join('\n').slice(0,1200);
        }
        fs.appendFileSync(outputPath,JSON.stringify(record)+'\n');
    }
    run.destroy();
    console.log(ch);
}
