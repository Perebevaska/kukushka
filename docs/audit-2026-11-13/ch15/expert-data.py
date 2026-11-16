"""Regenerate the three assets and independently check point-in-time data, decision economics and transfer.

Run under Python 3.12 with pandas, numpy, sklearn, joblib and a catalog from the course verifier.
"""
from contextlib import chdir
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_score

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site/data"
catalog = json.loads(Path(sys.argv[1]).read_text())
tasks = {(t["lesson"].split("/")[-1], t["id"]):t for t in catalog
         if t["lesson"].startswith("ch15/") and t["kind"] == "task"}

def generator(name):
    module = importlib.util.spec_from_file_location(name, ROOT / f"tools/{name}.py")
    code = importlib.util.module_from_spec(module)
    module.loader.exec_module(code)
    return code

def code(lesson, key, ns, parts=("setup","solution")):
    for part in parts:
        exec(compile(tasks[lesson,key][part],f"{lesson}/{key}/{part}","exec"),ns)

def values(frame, prob, retention=.5):
    monthly = frame.revenue_90 / 3
    return (retention * .35 * 12 * monthly).mul(prob) - (1500 + .2 * monthly)

def selected(frame, prob, retention=.5):
    profit = values(frame, prob, retention)
    return profit[profit.gt(0)].nlargest(150)

with tempfile.TemporaryDirectory() as tmp, chdir(tmp):
    source = generator("gen_data")
    source.OUT = Path(tmp)
    source.gen_chapter6(random.Random(6006))
    source.gen_chapter15(random.Random(15015))
    for file in ("guests_churn.csv","service_log.jsonl"):
        blob = Path(file).read_bytes()
        assert blob == (DATA/file).read_bytes(), file
        print("regenerated", file,sha256(blob).hexdigest())
    g = generator("gen_final2")
    g.DATA = Path(tmp)
    g.main()
    with sqlite3.connect("office.db") as regenerated, sqlite3.connect(DATA/"office.db") as supplied:
        for table in ("clients","contracts","orders","tickets","invoices"):
            query = f"SELECT * FROM {table} ORDER BY rowid"
            pd.testing.assert_frame_equal(pd.read_sql(query,regenerated),pd.read_sql(query,supplied))
        print("office.db logical identity all tables; supplied, regenerated sha256",
              *(sha256(p.read_bytes()).hexdigest() for p in (DATA/"office.db",Path("office.db"))))
    shutil.copyfile(DATA/"office.db","office.db")

    inc={}
    code("05-project","rollback",inc)
    code("05-project","timeline",inc)
    l=inc["log"]
    dates=pd.to_datetime(l.ts)
    wrong=l.loc[l.client.eq("app 3.2"),"payload"].map(lambda p:p.get("avg_check"))
    print("log dates, status, first 500/weekday, app3.2 and missing checks",
          dates.min(),dates.max(),l.status.value_counts().to_dict(),
          dates[l.status.eq(500)].min().day_name(),len(wrong),wrong.isna().sum(),l.columns.tolist())
    print("guests feature and 60-day outcome dates",pd.Timestamp("2026-12-01"),pd.Timestamp("2026-12-01")+pd.Timedelta(days=60))

    n={}
    code("06-final-project","models",n)
    train,test = n["train"],n["test"]
    cols=n["CAT"]+n["NUM"]
    mature=pd.concat([train,test],ignore_index=True)
    future=n["snapshot"]("2026-09-30")
    for label,frame in (("mature snapshots",mature),("production",future)):
        abnormal=frame.loc[frame.revenue_trend.abs()>1,["client_id","revenue_90","revenue_trend"]]
        print("revenue trend outside [-1,1]",label,len(abnormal),abnormal.head(2).to_dict("records"))
    db=sqlite3.connect("office.db")
    for owner,join,date_field in (("contract","contracts","start_date"),("client","clients","created_at")):
        sql=f"SELECT count(DISTINCT t.ticket_id),count(DISTINCT t.client_id) FROM tickets t JOIN {join} c USING(client_id) WHERE t.created_at<c.{date_field}"
        print("unique tickets, clients before",owner,db.execute(sql).fetchone())
    print("pre-creation tickets and clients active in June test lookback",db.execute("""
        SELECT COUNT(DISTINCT t.ticket_id),COUNT(DISTINCT t.client_id)
        FROM tickets t JOIN contracts co USING(client_id) JOIN clients cl USING(client_id)
        WHERE t.created_at < cl.created_at AND cl.is_test=0 AND co.start_date<='2026-06-30'
          AND (co.end_date IS NULL OR co.end_date>'2026-06-30')
          AND t.created_at>date('2026-06-30','-90 days') AND t.created_at<='2026-06-30'
        """).fetchone())
    for date,frame in mature.groupby("cutoff"):
        finish = date+pd.offsets.QuarterEnd()
        # Direct SQL uses civil-date membership and an independent calendar-quarter endpoint.
        target=pd.read_sql("""
            SELECT client_id, CASE WHEN end_date <= :end THEN 1 ELSE 0 END AS y
            FROM contracts JOIN clients USING (client_id)
            WHERE is_test = 0 AND start_date <= :cut AND (end_date IS NULL OR end_date > :cut)
            ORDER BY client_id
            """,db,params=dict(cut=date.date().isoformat(),end=finish.date().isoformat()))
        got=frame.sort_values("client_id")
        assert np.array_equal(got.churn,target.y) and np.array_equal(got.client_id,target.client_id)
        print("mature SQL labels",date.date(),finish.date(),len(got),got.churn.sum())
    print("production unknowns coded as zero",future.shape, future.churn.value_counts().to_dict(),
          "coverage until 2026-09-30, required through",pd.Timestamp("2026-09-30")+pd.offsets.QuarterEnd())
    c=pd.Timestamp("2026-06-30")
    uncut=n["build_features"](c)
    backup={k:n[k] for k in ("orders","tickets","invoices","base")}
    for key,col in (("orders","order_date"),("tickets","created_at"),("invoices","due_date")):
        n[key]=n[key][n[key][col].le(c)].copy()
    n["invoices"].loc[n["invoices"].paid_date.gt(c),"paid_date"]=pd.NaT
    n["base"]=n["base"].copy()
    n["base"].loc[n["base"].end_date.gt(c),"end_date"]=pd.NaT
    pd.testing.assert_frame_equal(uncut,n["build_features"](c))
    n.update(backup)
    print("future removed, all feature rows/columns equal",uncut.shape,"future orders incl. cancelled",
          n["orders"].order_date.gt(c).sum(),"known in train",test.client_id.isin(train.client_id).sum(),"/",len(test))
    final=n["final"]
    p=final.predict_proba(test[cols])[:,1]
    print("test AUROC AP mean-p prevalence Brier",roc_auc_score(test.churn,p),average_precision_score(test.churn,p),p.mean(),test.churn.mean(),brier_score_loss(test.churn,p))
    city=test.groupby("city").churn.agg(["size","sum","mean"])
    print("held-out city rates",city.round(4).to_dict("index"),"small-office plans",
          test.query("employees < 40").groupby("plan").churn.mean().round(4).to_dict())
    for name,m in n["models"].items():
        folds=cross_val_score(m,train[cols],train.churn,groups=train.client_id,cv=GroupKFold(5),scoring="average_precision")
        print("grouped AP",name,round(folds.mean(),4))
    for day in sorted(train.cutoff.unique())[1:]:
        early=train[train.cutoff.lt(day)]
        later=train[train.cutoff.eq(day)]
        f=clone(final).fit(early[cols],early.churn)
        pp=f.predict_proba(later[cols])[:,1]
        print("prospective",str(day)[:10],len(early),len(later),roc_auc_score(later.churn,pp),average_precision_score(later.churn,pp))
    base_calls=selected(test,p)
    rr=test.revenue_90/3
    idx=base_calls.index
    proxy=values(test,test.churn)
    print("test policy n caught expected proxy rule all none; retention break-even fixed list",
          len(idx),test.churn[idx].sum(),round(base_calls.sum()),round(proxy[idx].sum()),round(proxy[test.nsmallest(150,"revenue_trend").index].sum()),
          round(proxy.sum()),0,(1500+.2*rr[idx]).sum()/(test.churn[idx]*.35*12*rr[idx]).sum())
    for save in (.3,.5,.7):
        chosen=selected(test,p,save)
        factual=values(test,test.churn,save)
        print("sensitivity save / fixed calls profit / reoptimized n and profit",save,round(factual[idx].sum()),len(chosen),round(factual[chosen.index].sum()))
    code("06-final-project","package",n,("solution",))
    good=n["model"].predict_proba(future[cols])[:,1]
    polluted=pd.concat([mature,future],ignore_index=True)
    bad=clone(final).fit(polluted[cols],polluted.churn).predict_proba(future[cols])[:,1]
    print("legitimate final vs append pseudo-zeros: mean probability / call list count",
          (good.mean(),len(selected(future,good))),(bad.mean(),len(selected(future,bad))))
    destination=Path(tmp)/"transfer"
    destination.mkdir()
    shutil.copy("model.joblib",destination/"model.joblib")
    # Data-only output avoids carrying the features function, training variables or a notebook kernel.
    future[cols].iloc[:20].to_json(destination/"features.json",orient="table",double_precision=15)
    read="import joblib,pandas as pd,numpy as np; x=pd.read_json('features.json',orient='table'); np.save('out.npy',joblib.load('model.joblib').predict_proba(x)[:,1])"
    subprocess.run([sys.executable,"-I","-c",read],cwd=destination,check=True)
    delta=np.abs(np.load(destination/"out.npy")-good[:20]).max()
    assert delta<1e-12
    print("20 golden in separate interpreter from moved model/features, max delta",delta)
    db.close()
