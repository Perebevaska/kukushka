import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const indexURL = path.resolve('site/assets/vendor/pyodide') + '/';
const {loadPyodide} = await import(pathToFileURL(indexURL + 'pyodide.mjs'));
const py = await loadPyodide({indexURL});
const runner = 'docs/reaudit-2026-11-16/ch01/fixes/review-probes.py';
py.FS.mkdir('/repo');
py.FS.mount(py.FS.filesystems.NODEFS, {root: process.cwd()}, '/repo');
py.FS.writeFile('/tmp/export.json', fs.readFileSync(process.argv[2]));
console.log('Pyodide', py.version);
py.runPython(`import sys, runpy
sys.dont_write_bytecode=True
sys.argv=["/repo/${runner}","/tmp/export.json"]
try:
    runpy.run_path(sys.argv[0],run_name="__main__")
except SystemExit as exc:
    if exc.code: raise AssertionError(exc.code)`);
