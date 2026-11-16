// node expert-run.mjs COURSE_EXPORT OUTPUT_JSONL [after]
// Run in the course repository. Each lesson cell receives a new Python namespace.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
const [course, dest, phase='before'] = process.argv.slice(2);
const here=path.dirname(fileURLToPath(import.meta.url));
const vendor=path.resolve('site/assets/vendor/pyodide')+'/';
const {loadPyodide}=await import(pathToFileURL(vendor+'pyodide.mjs'));
const py=await loadPyodide({indexURL:vendor});
await py.loadPackage(['scikit-learn','pandas','matplotlib','joblib'],{messageCallback(){},errorCallback(){}});
for (const n of fs.readdirSync(path.join(here,'data-baseline'))) py.FS.writeFile(n,fs.readFileSync(path.join(here,'data-baseline',n)));
py.runPython(`import json, io, warnings, traceback, contextlib, matplotlib, sys, sklearn, numpy, pandas
matplotlib.use("agg")
import matplotlib.pyplot as plt
def capture(src):
    out=io.StringIO()
    try:
        with contextlib.redirect_stdout(out), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ctx={"__name__":"__main__"}
            exec(src,ctx)
        return json.dumps(dict(ok=True,out=out.getvalue().strip()),ensure_ascii=False)
    except Exception:
        return json.dumps(dict(ok=False,error=traceback.format_exc(limit=4),out=out.getvalue().strip()),ensure_ascii=False)
    finally:
        plt.close("all")`);
const run=py.globals.get('capture');
const items=JSON.parse(fs.readFileSync(course)).filter(i=>i.lesson.startsWith('ch07/'));
const tasks=new Set('forest-cm forest-prf roc-plot budget honest-t lr-bal knn-scale lasso gain both pairs bins combo rf-gain cv-models group-ratio save-load cv-table look groups missing time pipe trap metric grid final speed'.split(' '));
const extras={
 '01-confusion/forest-cm':'print(cm.tolist())',
 '02-precision-recall/forest-prf':'print(prec,rec,f1,bonuses)',
 '03b-money-threshold/budget':'print(t100,n_bonus,prec,rec)',
 '03b-money-threshold/honest-t':'print(t_val,profit_test,profit_05)',
 '05-scaling/knn-scale':'print(f1_raw,auc_raw,f1_sc,auc_sc)',
 '06b-feature-check/bins':'print(n_cols,auc_bins)',
 '06b-feature-check/combo':'print(auc_all,f1_all,f1_gain)',
 '09-project/grid':`from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import RandomForestClassifier
rf_auc=[]
for a,b in kf.split(X_train):
    train,val = X_train.iloc[a], X_train.iloc[b]
    truth = y_train.iloc[b]
    fitted = clone(grid.best_estimator_).fit(train, y_train.iloc[a])
    prob = fitted.predict_proba(val)[:,1]
    ranked = pd.DataFrame({'p':prob,'fact':truth, 'id':d.loc[val.index,'lead_id']}).sort_values(['p','id'],ascending=[False,True])
    k = int(.3*len(truth))
    rf = clone(pipe).set_params(model=RandomForestClassifier(n_estimators=50,min_samples_leaf=5,random_state=0,class_weight='balanced')).fit(train,y_train.iloc[a])
    rf_auc.append(roc_auc_score(truth,rf.predict_proba(val)[:,1]))
    print("fold size/deals/k/hits",len(truth),int(truth.sum()),k,int(ranked.head(k).fact.sum()))
print("RF balanced mean AUC",sum(rf_auc)/len(rf_auc))`,
 '03-threshold/roc-plot':`from sklearn.metrics import roc_curve, auc
for drop in (False,True):
    xx,yy,_=roc_curve(y_test,p,drop_intermediate=drop)
    print("vertices and area",drop,len(xx),auc(xx,yy))`,
 '09-project/final':`print("queue boundary", len(model_ids),model_ids[-1],len(rule_ids),rule_ids[-1], "rounded fraction budget",int(len(rule)*rule_share_test))
print("top30", round(model_catch*sum(y_test)), "equal k", round(model_same*sum(y_test)), round(rule_catch_test*sum(y_test)), "out of",sum(y_test))
print("fields",X_test.columns.tolist())`
};
function record(obj){fs.appendFileSync(dest,JSON.stringify(obj)+'\n')}
fs.writeFileSync(dest,'');
record({phase,runtime:py.version,python:py.runPython('sys.version'),sklearn:py.runPython('sklearn.__version__'),pandas:py.runPython('pandas.__version__'),numpy:py.runPython('numpy.__version__')});
for (const it of items) {
 if (process.argv[5] && !new RegExp(process.argv[5]).test(it.lesson+'/'+it.id)) continue;
 if (it.kind==='predict'||(it.kind==='task'&&!tasks.has(it.id))) continue;
 const id=it.lesson.slice(5)+'/'+it.id;
 const extra=extras[id]||'';
 const rateProbe=`X = pd.DataFrame({"city":["unique"+str(i) for i in range(50)]})
y = pd.Series([0,1]*25)
a = RateBy().fit_transform(X,y)
y.iloc[0] = 1
enc=RateBy()
b = enc.fit_transform(X,y)
print("first own label flip",a.iloc[0]["churn_rate_city"],b.iloc[0]["churn_rate_city"])
print("new key after fit",enc.transform(pd.DataFrame({"city":["new"]}))["churn_rate_city"].iloc[0],"global",y.mean())`;
 const source=it.kind==='cell'?it.code+(it.code.includes("class RateBy(")?'\n'+rateProbe:''):[it.setup,it.solution,extra].filter(Boolean).join('\n');
 record({id,kind:it.kind,...JSON.parse(run(source))});
}
const probes=fs.readFileSync(path.join(here,'expert-probes.py'),'utf8');
record({id:'independent',...JSON.parse(run(probes))});
