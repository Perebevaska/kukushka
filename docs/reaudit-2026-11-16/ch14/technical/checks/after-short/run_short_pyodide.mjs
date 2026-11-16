import fs from 'node:fs';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';
const base=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(base,'../../../../../..'),vendor=root+'/site/assets/vendor/pyodide/';
const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs'));const py=await loadPyodide({indexURL:vendor});await py.loadPackage(['numpy','pandas'],{messageCallback(){},errorCallback(){}});
for(const f of ['tasks.json','short_alerts.py'])py.FS.writeFile('/home/pyodide/'+f,fs.readFileSync(base+'/'+f));
py.runPython('__file__="/home/pyodide/short_alerts.py"\n'+fs.readFileSync(base+'/short_alerts.py','utf8'));
