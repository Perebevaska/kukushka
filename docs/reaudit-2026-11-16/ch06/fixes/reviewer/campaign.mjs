import {readFileSync,writeFileSync} from "node:fs";
import {resolve,dirname} from "node:path";
import {pathToFileURL,fileURLToPath} from "node:url";
const here=dirname(fileURLToPath(import.meta.url)), root=resolve(here,"../../../../..");
const runtime=resolve(root,"site/assets/vendor/pyodide")+"/";
const {loadPyodide}=await import(pathToFileURL(runtime+"pyodide.mjs"));
const py=await loadPyodide({indexURL:runtime});
await py.loadPackage(["scikit-learn","pandas"],{messageCallback(){}});
for (const name of ["guests_churn.csv","deliveries.csv"]) {
    py.FS.writeFile("/home/pyodide/"+name,readFileSync(resolve(root,"site/data",name)));
}
writeFileSync(resolve(here,"campaign.json"),py.runPython(readFileSync(resolve(here,"campaign.py"),"utf8"))+"\n");
