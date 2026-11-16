/* Execute previously extracted public lesson-data in the browser's bundled Pyodide. */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here,"../../../../..");
const [casesFile,output,...names] = process.argv.slice(2);
const rows = JSON.parse(fs.readFileSync(casesFile,"utf8"))
  .filter(row => !names.length || names.includes(row.id));
const vendor=path.join(root,"site/assets/vendor/pyodide")+"/";
const {loadPyodide}=await import(pathToFileURL(vendor+"pyodide.mjs").href);
const py=await loadPyodide({indexURL:vendor});
await py.loadPackage(["numpy","pandas","matplotlib","scikit-learn"],{messageCallback(){}});
const cwd="/home/pyodide/";
py.FS.writeFile(cwd+"harness.py",fs.readFileSync(path.join(root,"site/assets/harness.py")));
for(const f of new Set(rows.flatMap(row=>row.files))) {
  py.FS.writeFile(cwd+f,fs.readFileSync(path.resolve(here,"../../technical/data-baseline",f)));
}
const run=py.runPython("import sys;sys.path.insert(0,'/home/pyodide');import harness;harness.run");
fs.writeFileSync(output,"");
for(const row of rows) {
 const result=run(row.code,row.check,row.setup);
 const obj=result.toJs({dict_converter:Object.fromEntries});result.destroy();
 const emitted={id:row.id,expected:row.expected,observed:obj.check.passed,check_sha256:row.check_sha256,msg:obj.check.msg,error:obj.error,stdout:obj.out.slice(-400)};
 fs.appendFileSync(output,JSON.stringify(emitted)+"\n");
 console.log(row.id,row.expected,obj.check.passed,obj.check.msg.slice(0,110));
}
