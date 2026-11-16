import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const folder = join(process.cwd(), 'site/assets/vendor/pyodide') + '/';
const { loadPyodide } = await import(pathToFileURL(folder + 'pyodide.mjs'));
const py = await loadPyodide({indexURL: folder});
await py.loadPackage('pandas', {messageCallback() {}});
const item = JSON.parse(readFileSync(process.argv[2], 'utf8')).find(
    t => t.lesson === 'ch03/03-types' && t.kind === 'predict' && t.id === 'q3'
);
py.runPython('import pandas as pd, sys\nprint(sys.version.split()[0], pd.__version__)');
py.runPython(item.code);
py.runPython(`iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
ru = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
print(*iso.fillna(ru).dt.date)`);
