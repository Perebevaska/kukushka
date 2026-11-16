import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const artifact = fileURLToPath(new URL('.', import.meta.url));
const root = resolve(artifact, '../../../..');
const indexURL = resolve(root, 'site/assets/vendor/pyodide') + '/';
const { loadPyodide } = await import(pathToFileURL(indexURL + 'pyodide.mjs'));
const py = await loadPyodide({ indexURL, env: { MPLBACKEND: "agg" } });
await py.loadPackage(['pandas','scikit-learn','matplotlib']);
const data = process.argv[3] || resolve(root, 'site/data');
for (const name of ['deliveries','guest_orders','guests_churn','guests_churn_dates','guests_current'])
  py.FS.writeFile(name + '.csv', readFileSync(resolve(data, name + '.csv')));
py.FS.writeFile('depth.json', readFileSync(resolve(root, 'content/widgets/tree-depth.json')));
const target = process.argv[4] || artifact;
const profile = py.runPython(readFileSync(resolve(artifact, 'expert-data.py'), 'utf8'));
writeFileSync(resolve(target, 'expert-data.json'), profile + '\n');
if (process.argv[2]) {
  const records = JSON.parse(readFileSync(process.argv[2], 'utf8')).filter(x => x.lesson.startsWith('ch06/') && ['cell','predict'].includes(x.kind));
  py.runPython('import contextlib,io,warnings,matplotlib.pyplot as plt,pandas as pd\ndef render_example(src):\n env = {}\n out=io.StringIO()\n with contextlib.redirect_stdout(out),warnings.catch_warnings():\n  warnings.simplefilter("ignore")\n  try: exec(src,env)\n  except Exception as e: print(type(e).__name__, str(e))\n plt.close("all")\n return out.getvalue().strip()');
  const run = py.globals.get('render_example');
  const outputs = records.map(({lesson,id,kind,code}) => ({lesson,id,kind,output:run(code)}));
  writeFileSync(resolve(target, 'expert-examples.json'), JSON.stringify(outputs,null,2)+'\n');
}
