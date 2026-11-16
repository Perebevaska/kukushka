"""Execute the delivered notebook in an empty directory and corroborate its outputs."""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import nbformat
from nbclient import NotebookClient
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve().parent
CH = HERE.parent.parent
input_dir = Path(sys.argv[1]).resolve()
tag = sys.argv[2]
def digest(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()
with TemporaryDirectory() as temp:
    p = Path(temp)
    src = input_dir/"churn.ipynb"
    shutil.copy(src,p/src.name)
    shutil.copytree(input_dir/"data",p/"data")
    nb = nbformat.read(p/src.name,as_version=4)
    code = [cell for cell in nb.cells if cell.cell_type=="code"]
    for cell in code:
        cell.outputs = []
        cell.execution_count = None
    nbformat.write(nb,p/src.name)
    os.environ.update(IPYTHONDIR=str(p/"ipy"),JUPYTER_RUNTIME_DIR=str(p/"runtime"),MPLCONFIGDIR=str(p/"mpl"))
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]
    client = NotebookClient(nb,timeout=600,kernel_name="python3",resources={"metadata":{"path":str(p)}})
    client.execute()
    out = p/"project-output"
    summary = json.loads((out/"test-summary.json").read_text())
    choice = json.loads((out/"selection-before-test.json").read_text())
    scores = pd.read_csv(out/"fresh-campaign.csv")
    hist = pd.read_csv(p/"data/guests_churn.csv")
    fresh = pd.read_csv(p/"data/guests_current.csv")
    dates = pd.read_csv(p/"data/guests_churn_dates.csv")
    Xraw = hist.drop(columns=["guest_id","churned","card_blocked"])
    def design(x, known=None):
        x=x.copy()
        x["no_visits"] = x["visits_90d"].eq(0).astype(int)
        x["avg_check"] = x.avg_check.fillna(0)
        x=pd.get_dummies(x,dtype=int)
        return x if known is None else x.reindex(columns=known,fill_value=0)
    train,test = train_test_split(hist.index,random_state=42,test_size=.25,stratify=hist.churned)
    def forest(rows):
        x=design(Xraw.loc[rows])
        m=RandomForestClassifier(n_estimators=100,min_samples_leaf=3,random_state=0).fit(x,hist.loc[rows,"churned"])
        return m,x.columns
    model,cols=forest(train)
    xt=design(Xraw.loc[test],cols)
    result=hist.loc[test,["guest_id","churned","days_since_last"]].copy()
    result["risk"] = model.predict_proba(xt)[:,1]
    def rank(df,field,k):
        return df.sort_values([field,"guest_id"],ascending=[False,True]).head(k)
    top = rank(result,"risk",60)
    rule = rank(result,"days_since_last",60)
    full,cols=forest(hist.index)
    xf=design(fresh.drop(columns=["snapshot_date","guest_id"]),cols)
    check = fresh.assign(risk=full.predict_proba(xf)[:,1])
    queue = rank(check,"risk",int(len(check)*.10))
    exact_order = queue.guest_id.tolist()==scores.guest_id.tolist()
    same_risk = np.allclose(queue.risk,scores.risk,rtol=0,atol=1e-12)
    metrics = {"accuracy":model.score(xt,hist.loc[test,"churned"]),"model_top_rate":top.churned.mean(),"rule_top_rate":rule.churned.mean(),"capture":top.churned.sum()/result.churned.sum(),"top_lift":top.churned.mean()/result.churned.mean()}
    assert all(abs(summary[k]-v)<1e-12 for k,v in metrics.items())
    assert exact_order and same_risk and choice["winner"]=="лес"
    m = hist.merge(fresh,on="guest_id",suffixes=("_oct","_dec"))
    last = pd.to_datetime(m.snapshot_date) - pd.to_timedelta(m.days_since_last_dec,unit="D")
    conflict = int((m.churned.eq(1)&last.ge("2026-10-01")&last.lt("2026-11-30")).sum())
    never_visited = int((m.churned.eq(0)&last.lt("2026-10-01")).sum())
    record = dict(delivered_files={f.name:digest(f) for f in [src,*sorted((p/"data").glob("*.csv"))]},
        clean_code_cells=len(code), execution_counts=[c.execution_count for c in code],
        compared_scores=metrics,choice=choice["winner"],cv_accuracy=choice["CV"]["mean"],cv_std=choice["CV"]["std"],train=len(train), test=len(test),test_churns=int(result.churned.sum()),top_churns=int(top.churned.sum()),rule_churns=int(rule.churned.sum()),
        production_fit_rows=len(hist),production_scored=len(fresh),campaign_size=len(scores),same_risks=bool(same_risk),same_queue=exact_order,selected_overlap=int(len(set(top.guest_id)&set(rule.guest_id))),production_score_date=fresh.snapshot_date.unique().tolist(),
        historical_current_id_overlap=len(m),contradictory_last_visit_for_churns=conflict,contradictory_missing_visit=never_visited,
        generated_files=sorted(f.name for f in out.iterdir()), versions={"python":sys.version,"sklearn":__import__("sklearn").__version__,"pandas":pd.__version__})
    for f in ("test-summary.json","fresh-campaign.csv"):
        assert (out/f).read_bytes()==(input_dir/"project-output"/f).read_bytes(), f
    if tag == "after":
        card_output = "fresh-campaign-card-train75.csv"
        card = pd.read_csv(out/card_output)
        assert (out/card_output).read_bytes()==(input_dir/"project-output"/card_output).read_bytes()
        card_train = pd.get_dummies(Xraw.fillna({"avg_check":0}),dtype=int)
        card_m = RandomForestClassifier(n_estimators=100,min_samples_leaf=3,random_state=0).fit(card_train.loc[train],hist.loc[train,"churned"])
        candidates = pd.get_dummies(fresh.drop(columns=["snapshot_date","guest_id"]).fillna({"avg_check":0}),dtype=int).reindex(columns=card_train.columns,fill_value=0)
        reference = rank(fresh.assign(risk=card_m.predict_proba(candidates)[:,1]),"risk",int(len(fresh)*.1))
        assert reference.guest_id.tolist()==card.guest_id.tolist()
        assert np.allclose(reference.risk,card.risk,rtol=0,atol=1e-12)
        assert summary["version"]=="analysis-v2-cv75" and scores.model_version.eq("production-v2-full100").all() and card.model_version.eq("card-v2-train75").all()
        assert not len(m) and len(scores)==len(card)==240
        record.update(artifact_bytes_match=True,historical_version=summary["version"],production_version=scores.model_version.iloc[0],card_version=card.model_version.iloc[0],card_fit_rows=len(train),card_queue_size=len(card),card_risks_match=True,card_order_matches=True,card_and_production_queue_overlap=len(set(card.guest_id)&set(scores.guest_id)))
    (HERE/f"received-{tag}.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(record,ensure_ascii=False))
