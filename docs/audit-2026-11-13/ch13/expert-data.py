"""Reproduce chapter 13 inputs and recover the simulator's held-back topic and sentiment."""
import ast
import importlib.util
from pathlib import Path
import random
import tempfile

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,cohen_kappa_score,confusion_matrix,f1_score
from sklearn.model_selection import StratifiedGroupKFold,train_test_split,cross_val_score
from sklearn.pipeline import make_pipeline

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/"site/data"
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/f"tools/{name}.py")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

generator=load("gen_data")
# Only record existing simulator variables, without drawing additional random values.
import inspect
source=inspect.getsource(generator.gen_chapter13)
source=source.replace("        rows.append([f'R-", "        train_state.append((kind,topic))\n        rows.append([f'R-")
source=source.replace("        new_rows.append([d.isoformat(), shop, typo2(text)])",
                      "        new_rows.append([d.isoformat(), shop, typo2(text)])\n        new_state.append((*new_rows[-1],kind,topic))")
with tempfile.TemporaryDirectory() as tmp:
    dpath=Path(tmp)
    ns=dict(generator.__dict__,OUT=dpath,train_state=[],new_state=[])
    exec(compile(source,"audited-generator","exec"),ns)
    ns["gen_chapter13"](random.Random(13013))
    for module in ("gen_labels","gen_lemmas"):
        mod=load(module)
        mod.ROOT=mod.DATA=dpath
        mod.main()
    for name in ["reviews_text","reviews_new","review_labels","review_gold","review_lemmas"]:
        file=name+".csv"
        assert (dpath/file).read_bytes()==(DATA/file).read_bytes()
        print("exact bytes",name)

r=pd.read_csv(DATA/"reviews_text.csv")
n=pd.read_csv(DATA/"reviews_new.csv")
truth=pd.DataFrame(sorted(ns["new_state"],key=lambda row:row[0]),
                   columns=["date","shop_id","text","sim_kind","sim_topic"])
for k in ["date","shop_id","text"]: assert n[k].equals(truth[k])
r["sim_neg"]=[kind!="pos" for kind,topic in ns["train_state"]]
n=n.assign(sim_neg=truth.sim_kind!="pos",sim_topic=truth.sim_topic)
y=r.rating<=3
print("dataset",[(len(a),a.review_id.nunique(),a.text.nunique(),int(a.isna().sum().sum())) for a in [r,n]])
print("new overlap training, period",n.text.isin(r.text).sum(),n.date.min(),n.date.max())
print("training binary proxy mismatches",int((y!=r.sim_neg).sum()), "ratings",r.rating.value_counts().sort_index().to_dict(),"topics", r.topic.value_counts().to_dict())
def model():
    return make_pipeline(TfidfVectorizer(ngram_range=(1,2)),LogisticRegression(max_iter=1000))
for name, labels in [("sent",y),("topic",r.topic)]:
    a,b=train_test_split(r.index,test_size=.25,random_state=42,stratify=labels)
    h=model().fit(r.text[a],labels[a]).predict(r.text[b])
    seen=r.text[b].isin(r.text[a])
    print("holdout",name,"acc,duplicates,n",accuracy_score(labels[b],h),seen.sum(),len(b))
    print("acc on seen/unseen",accuracy_score(labels[b][seen],h[seen]),accuracy_score(labels[b][~seen],h[~seen]))
    cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42)
    print("exact-text grouped five-fold",name,cross_val_score(model(),r.text,labels,groups=r.text,cv=cv).round(4))
    if name=="sent":
        tn,fp,fn,tp=confusion_matrix(y[b],h).ravel()
        tpr=tp/(fn+tp); fpr=fp/(fp+tn)
    else: print("topic per-class F1",dict(zip(np.unique(labels),f1_score(labels[b],h,average=None).round(3))))
# More demanding stress-test: keep out a whole main-phrase family reconstructed from the generator.
tree=ast.parse(source)
phrase_sets={v.targets[0].id:ast.literal_eval(v.value) for v in ast.walk(tree)
             if isinstance(v,ast.Assign) and isinstance(v.targets[0],ast.Name) and v.targets[0].id in ["pos","neg"]}
# For simple single-clause texts specifically, strip the generator's wrappers; use exact phrase membership only.
main_clause=[]
for text in r.text.str.lower():
    clauses=[p.strip() for p in text.replace("!",".").split(".") if p.strip()]
    candidates=[p for p in clauses if any(p in phrases for by_topic in phrase_sets.values() for phrases in by_topic.values())]
    main_clause.append(candidates[0] if len(candidates)==1 else None)
one=r.assign(phrase=main_clause).dropna(subset=["phrase"])
for label in ["sim_neg","topic"]:
    cv=StratifiedGroupKFold(n_splits=5,random_state=42,shuffle=True)
    print("phrase-held-out, exact one-clause",label,len(one),one.phrase.nunique(),
          cross_val_score(model(),one.text,one[label],groups=one.phrase,cv=cv).round(3))

sent=model().fit(r.text,y)
topic=model().fit(r.text,r.topic)
n["neg"]=sent.predict(n.text)
n["topic"]=topic.predict(n.text)
n["period"]=np.where(n.date<"2026-10-05","before","after")
print("new latent text truth accuracy",accuracy_score(n.sim_neg,n.neg),accuracy_score(n.sim_topic,n.topic))
kc=n[n.shop_id=="KZN-2"]
print("source TPR/FPR",tpr,fpr)
for period,k in kc.groupby("period",sort=False):
    obs=k.neg.mean()
    tn2,fp2,fn2,tp2=confusion_matrix(k.sim_neg,k.neg).ravel()
    print("KZN",period,"n, observed, adjusted, latent, latent TPR/FPR",len(k),obs,(obs-fpr)/(tpr-fpr),k.sim_neg.mean(),tp2/(tp2+fn2),fp2/(fp2+tn2))
    print("delivery share among complaints, predicted and latent",k[k.neg].topic.eq("доставка").mean(),k[k.sim_neg].sim_topic.eq("доставка").mean())
print("mean share by shop",n.groupby(["shop_id","period"]).neg.agg(["mean","size"]).round(3).to_string())
print("KZN weekly",kc.set_index(pd.to_datetime(kc.date)).neg.resample("W-SUN").agg(["sum","size","mean"]).round(3).to_string())

labels=pd.read_csv(DATA/"review_labels.csv").pivot(index="review_id",columns="annotator",values="label")
gold=pd.read_csv(DATA/"review_gold.csv").set_index("review_id").label
print("annotators/gold",labels.shape,len(gold),labels.loc[gold.index].eq(gold,axis=0).mean().to_dict())
print("gold equals original topic",r.set_index("review_id").topic.loc[gold.index].eq(gold).all(),
      "unanimous, three different",labels.nunique(axis=1).value_counts().to_dict())
print("kappa AB AV BV",*[round(cohen_kappa_score(labels.iloc[:,a],labels.iloc[:,b]),3) for a,b in [(0,1),(0,2),(1,2)]])

checked=r.sample(200,random_state=5)
topics=["кофе","еда","обслуживание","доставка","цена","атмосфера"]
rand=random.Random(15)
llm=[]
for true in checked.topic:
    v=rand.random()
    if v<.04: label=None
    elif v<.06: label="сервис"
    elif v<(.30 if true=="атмосфера" else .16): label=rand.choice([c for c in topics if c!=true])
    else: label=true
    llm.append(label)
rest=r.drop(checked.index)
h=make_pipeline(TfidfVectorizer(),LogisticRegression(max_iter=1000)).fit(rest.text,rest.topic).predict(checked.text)
yes=np.asarray(llm)==checked.topic.to_numpy()
base=h==checked.topic.to_numpy()
left=(yes & ~base).sum();right=(base & ~yes).sum()
delta=yes.astype(int)-base.astype(int)
boot=np.random.default_rng(777).choice(delta,(10000,len(delta))).mean(1)
print("LLM paired",yes.sum(),base.sum(),left,right,"exact binomial",binomtest(left,left+right).pvalue,
      "paired diff bootstrap",np.quantile(boot,[.025,.975]),"invalid",sum(x not in topics for x in llm))

from sklearn.metrics import precision_score, recall_score
a,b=train_test_split(r.index,test_size=.25,random_state=42,stratify=y)
fit,cal=train_test_split(a,test_size=1/3,random_state=42,stratify=y[a])
svc=make_pipeline(TfidfVectorizer(),LogisticRegression(max_iter=1000)).fit(r.text[fit],y[fit])
pv=svc.predict_proba(r.text[cal])[:,1]
thr=max(v for v in np.arange(.05,.96,.01) if recall_score(y[cal],pv>=v)>=.95)
score=svc.predict_proba(r.text[b])[:,1] >= thr
print("independent validation-selected threshold, final precision, recall, flagged",thr,precision_score(y[b],score),recall_score(y[b],score),score.sum())

# Derive public label() verbatim, with mocked Messages and no API key/call.
from types import SimpleNamespace
lesson=(ROOT/"content/ch13/04c-llm.md").read_text()
sample="def label(text):" + lesson.split("def label(text):",1)[1].split("print(label",1)[0]
f=ast.parse(sample)
fn={}
for reason,blocks in [("max_tokens",[]),("end_turn",[]),("end_turn",[SimpleNamespace(type="text",text='{}')])]:
    def create(**kw): return SimpleNamespace(stop_reason=reason,content=blocks)
    fn.update(client=SimpleNamespace(messages=SimpleNamespace(create=create)),MODEL="mock",PROMPT="test")
    exec(compile(f,"lesson-label","exec"),fn)
    try: print("API fixture",reason,len(blocks),fn["label"]("тест"))
    except StopIteration: print("API fixture",reason,len(blocks),"StopIteration")

for example in ["Перепутали заказ.", "Заказ не перепутали.", "Кофе был горячим.",
                "Кофе был не горячим.", "Курьер приехал вовремя.", "Курьер не приехал."]:
    print("novel test",example,f"{sent.predict_proba([example])[0,1]:.3f}",topic.predict([example])[0])
